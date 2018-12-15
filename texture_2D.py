#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from get_data import getData
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import numpy as np
from sklearn.decomposition import PCA
from int_features_2D import getIntensityFeatures
from texture_features_2D import getTextureFeatures
from show_images import showImages

"""
Run
===============================================================================
""" 
def run(mode = "default"):
    if mode == "default": 
        train_x, train_masks, train_y, val_x, val_masks, val_y, test_x, test_masks, test_y = getData()
        getTexture(train_x, train_masks, train_y, val_x, val_masks, val_y, test_x, test_masks, test_y)
        
    elif mode == "cross_val":
        cv_train_x, cv_train_masks, cv_train_y , cv_val_x, cv_val_masks, cv_val_y, test_x, test_masks, test_y = getData("cross_val")
        for train_x, train_masks, train_y, val_x, val_masks, val_y  in zip(cv_train_x, cv_train_masks, cv_train_y, cv_val_x, cv_val_masks, cv_val_y):
            getTexture(train_x, train_masks, train_y, val_x, val_masks, val_y, test_x, test_masks, test_y)

    
"""
Normalize data
===============================================================================
"""  
def normalizeData(train_slices, train_slices_masks):
    all_px = []
    for nodule, mask in zip(train_slices, train_slices_masks):
        all_px.append(nodule[mask == 1])  
    all_px = np.hstack(all_px)
    mean_int = np.mean(all_px)
    std_int = np.std(all_px)
    
    return mean_int, std_int
 
"""
Get Prediction
===============================================================================
"""
def getPrediction(train_features, train_y, features, labels):
    modelSVM = SVC(kernel = 'linear', gamma = 'auto', decision_function_shape= 'ovo',class_weight='balanced')
    modelSVM.fit(train_features, train_y)
    predictSVM = modelSVM.predict(features)

    accuracy = accuracy_score(labels, predictSVM)
    print("Accuracy SVM = %.3f" % accuracy)

    return predictSVM

def confusionMatrix(predictions, labels):
    true_positives = 0
    false_negatives = 0
    false_positives = 0
    true_negatives = 0
    
    for i in range(len(predictions)):
        if predictions[i] == labels[i] :
            if  predictions[i] == 1.0:
                true_positives += 1
            elif  predictions[i] == 0.0:
                true_negatives += 1
        elif predictions[i] != labels[i]:
            if predictions[i] == 1.0:
                false_positives += 1
            elif predictions[i] == 0.0:
                false_negatives += 1
                
    return np.asarray([[true_positives, false_negatives], [false_positives, true_negatives]]) 
    
def getPerformanceMetrics(predictions_outer_lung, labels_outer_lung):
    c_matrix_outer_lung = confusionMatrix(predictions_outer_lung, labels_outer_lung)
    
    true_positives = c_matrix_outer_lung[0,0]
    false_negatives = c_matrix_outer_lung[0,1]
    false_positives = c_matrix_outer_lung[1,0]
    true_negatives = c_matrix_outer_lung[1,1]

    accuracy = (true_positives + true_negatives)/(true_positives + true_negatives + false_positives + false_negatives)
    
    dice = (2*true_positives/(false_positives+false_negatives+(2*true_positives)))
    jaccard = (true_positives)/(true_positives+false_positives+false_negatives)
    matrix = np.asarray([[true_positives, false_negatives], [false_positives, true_negatives]])
    
    return dice, jaccard, matrix, accuracy 

def separateClasses(predictSVM):
    solid =[] # label 2
    sub_solid = [] # label 1
    non_solid = [] # label 0
    for j in range(len(predictSVM)):
        if predictSVM[j] == 0:
            non_solid.append(1)
        else: 
            non_solid.append(0)
            
        if predictSVM[j] == 1:
            sub_solid.append(1)
        else: 
            sub_solid.append(0)
            
        if predictSVM[j] == 2:
            solid.append(1)
        else: 
            solid.append(0)
            
    return solid, sub_solid, non_solid

def textureMetrics (prediction, val_y):
    solid_pred, sub_solid_pred, non_solid_pred = separateClasses(prediction)
    solid_label, sub_solid_label, non_solid_label = separateClasses(val_y)
    
    dice_solid, jaccard_solid, matrix_solid, accuracy_solid = getPerformanceMetrics(solid_pred, solid_label)
    dice_sub_solid, jaccard_sub_solid, matrix_sub_solid, accuracy_sub_solid = getPerformanceMetrics(sub_solid_pred, sub_solid_label)
    dice_non_solid, jaccard_non_solid, matrix_non_solid, accuracy_non_solid = getPerformanceMetrics(non_solid_pred, non_solid_label)
    
    print("Solid texture: The dice value is %.2f and the jaccard value is %.2f. The accuracy is %.2f" % (dice_solid, jaccard_solid, accuracy_solid))
    print("Sub solid texture: The dice value is %.2f and the jaccard value is %.2f. The accuracy is %.2f" % (dice_sub_solid, jaccard_sub_solid, accuracy_sub_solid))
    print("Non solid texture: The dice value is %.2f and the jaccard value is %.2f. The accuracy is %.2f" % (dice_non_solid, jaccard_non_solid, accuracy_non_solid))
   
    

"""
Get Texture
===============================================================================
"""  
           
def getTexture(train_x, train_masks, train_y, val_x, val_masks, val_y, test_x, test_masks, test_y):
    
    mean_int, std_int = normalizeData(train_x, train_masks)
    train_x = (train_x - mean_int)/std_int
    val_x = (val_x - mean_int)/std_int
    test_x = (test_x - mean_int)/std_int
    
    train_int, val_int, test_int, train_circ, val_circ, test_circ = getIntensityFeatures(train_x, train_masks, val_x, val_masks, test_x, test_masks)
    train_gabor, val_gabor, test_gabor,train_lbp, val_lbp, test_lbp = getTextureFeatures(train_x, train_masks, val_x, val_masks, test_x, test_masks)
    
    """
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    print("\nIntensity Features only \n=======================")
    prediction_int = getPrediction(train_int ,train_y, val_int , val_y)
    #texture_metrics(prediction_int, val_y)
    
    print("\nCircular Features only \n=======================")
    prediction_circ = getPrediction(train_circ, train_y, val_circ, val_y)
    #texture_metrics(prediction_circ, val_y)
    
    print("\nLBP Features only \n=======================")
    prediction_lbp = getPrediction(train_lbp, train_y, val_lbp, val_y)
    #texture_metrics(prediction_lbp, val_y)
    
    print("\nGabor Features only \n=======================")
    prediction_gb = getPrediction(train_gabor, train_y, val_gabor, val_y)
    #texture_metrics(prediction_gb, val_y)
    """ 
    print("\nAll Features\n=======================")
    train_features = np.concatenate((train_int, train_circ,train_lbp, train_gabor), axis=1)
    val_features = np.concatenate((val_int, val_circ, val_lbp, val_gabor), axis=1)
    test_features = np.concatenate((test_int, test_circ, test_lbp, test_gabor), axis=1)
    prediction_all = getPrediction(train_features, train_y, val_features, val_y)
    #texture_metrics(prediction_all, val_y)
    
    print("\n(PCA) All Features\n=======================")
    pca = PCA(n_components = 8)
    train_int_pca = np.concatenate((train_int, train_circ), axis = 1)
    val_int_pca = np.concatenate((val_int, val_circ), axis = 1)
    pca.fit_transform(train_int_pca)
    pca.fit_transform(val_int_pca)
    
    pca = PCA(n_components = 8)
    train_text_pca = np.concatenate((train_lbp, train_gabor), axis = 1)
    val_text_pca = np.concatenate((val_lbp, val_gabor), axis = 1)
    pca.fit_transform(train_text_pca)
    pca.fit_transform(val_text_pca)
   
    prediction_all_pca = getPrediction(np.concatenate((train_int_pca, train_text_pca), axis = 1), train_y,np.concatenate((val_int_pca, val_text_pca), axis = 1), val_y)
    texture_metrics(prediction_all_pca, val_y)
 
    """
    for i in range(len(val_x)):
        showImages([val_x[i]], [val_masks[i]], nodules_and_mask = True, overlay = False)
        
        print("Intensity = %.0f" % prediction_int[i])
        print("Circular = %.0f" % prediction_circ[i])
        #print("Shape = %.0f" % prediction_shape[i])
        print("LBP = %.0f" % prediction_lbp[i])
        print("All = %.0f" % prediction_all[i])
        print("All (PCA) = %.0f" % prediction_all_pca[i])
        print("GT = %.0f" % val_y[i])
    
    """
    
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    print("TEST SET")
    
    print("\nIntensity Features only \n=======================")
    #prediction_int = getPrediction(train_int ,train_y, test_int , test_y)
    #textureMetrics(prediction_int, test_y)
        
    print("\nCircular Features only \n=======================")
    prediction_circ = getPrediction(train_circ, train_y, test_circ, test_y)
    #textureMetrics(prediction_circ, test_y)
    
    print("\nLBP Features only \n=======================")
    prediction_lbp = getPrediction(train_lbp, train_y, test_lbp, test_y)
    #textureMetrics(prediction_lbp, test_y)
        
    print("\nGabor Features only \n=======================")
    prediction_gb = getPrediction(train_gabor, train_y, test_gabor, test_y)
    #textureMetrics(prediction_gb, test_y)
      
    print("\nAll Features\n=======================")
    train_features = np.concatenate((train_int, train_circ,train_lbp, train_gabor), axis=1)
    test_features = np.concatenate((test_int, test_circ, test_lbp, test_gabor), axis=1)
    prediction_all = getPrediction(train_features, train_y, test_features, test_y)
    textureMetrics(prediction_all, test_y)
        
    print("\n(PCA) All Features\n=======================")
    pca = PCA(n_components = 4)
    train_int_pca = np.concatenate((train_int, train_circ), axis = 1)
    test_int_pca = np.concatenate((test_int, test_circ), axis = 1)
    pca.fit_transform(train_int_pca)
    pca.fit_transform(test_int_pca)
        
    pca = PCA(n_components = 4)
    train_text_pca = np.concatenate((train_lbp, train_gabor), axis = 1)
    test_text_pca = np.concatenate((test_lbp, test_gabor), axis = 1)
    pca.fit_transform(train_text_pca)
    pca.fit_transform(test_text_pca)
       
    prediction_all_pca = getPrediction(np.concatenate((train_int_pca, train_text_pca), axis = 1), train_y,np.concatenate((test_int_pca, test_text_pca), axis = 1), test_y)
    textureMetrics(prediction_all_pca, test_y)
    

run()