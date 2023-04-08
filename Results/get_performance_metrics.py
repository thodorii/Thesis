from absl import app, flags
import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from transunet import TransUNet
import sys
sys.path.append('../Thesis')
from DatasetHelpers.Dataset import create_dataset, convert_to_tfds

FLAGS = flags.FLAGS
flags.DEFINE_bool("debug", False, "Set logging level to debug")
flags.DEFINE_integer("scenario", 1, "Training data scenario. \n\t 1: Only co_event \n\t 2: coevent & preevent \n\t 3: coevent & preevent & coherence")
flags.DEFINE_string("model_path", "/workspaces/Thesis/Results/Models/unet_scenario1_64", "'xgboost', 'unet', 'a-unet")
flags.DEFINE_string('s1_co', '/workspaces/Thesis/10m_data/s1_co_event_grd', 'filepath of Sentinel-1 coevent data')
flags.DEFINE_string('s1_pre', '/workspaces/Thesis/10m_data/s1_pre_event_grd', 'filepath of Sentinel-1 prevent data')
flags.DEFINE_string('s2_weak', '/workspaces/Thesis/10m_data/s2_labels', 'filepath of S2-weak labelled data')
flags.DEFINE_string('coh_co', '/workspaces/Thesis/10m_data/coherence/co_event', 'filepath of coherence coevent data')
flags.DEFINE_string('coh_pre', '/workspaces/Thesis/10m_data/coherence/pre_event', 'filepath of coherence prevent data')

flags.DEFINE_string('hand_coh_co', '/workspaces/Thesis/10m_hand/coherence_10m/hand_labeled/co_event', '(h) filepath of coevent data')
flags.DEFINE_string('hand_coh_pre', '/workspaces/Thesis/10m_hand/coherence_10m/hand_labeled/pre_event', '(h) filepath of preevent data')
flags.DEFINE_string('hand_s1_co', '/workspaces/Thesis/10m_hand/HandLabeled/S1Hand', '(h) filepath of Sentinel-1 coevent data')
flags.DEFINE_string('hand_s1_pre', '/workspaces/Thesis/10m_hand/S1_Pre_Event_GRD_Hand_Labeled', '(h) filepath of Sentinel-1 prevent data')
flags.DEFINE_string('hand_labels', '/workspaces/Thesis/10m_hand/HandLabeled/LabelHand', 'filepath of hand labelled data')
'''
THIS FILE IS INTENDED TO RUN A PRETRAINED MODEL THROUGH TESTING.

To verify performance of the models, we must test them on
1. The hold out (default: sri-lanka) test dataset (weakly labelled)
2. The hand labelled test dataset.

Performance metrics for each test must include
1. Total mIoU
2. Water mIoU
3. Water Precision
4. Water Recall
5. Water F1
6. Nonwater mIoU
7. Nonwater Precision
8. Nonwater Recall
9. Nonwater F1
'''

'''
IoU = TP / (TP + FP + FN)
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
'''

def main(x):
    # USING: Saving whole models so that the architecture does not need to be initialized.
    # IGNORE:  when restoring a model from weights-only, create a model with the same architecture as the original model and then set its weights.

    model = tf.keras.models.load_model(FLAGS.model_path)
    dataset = create_dataset(FLAGS)
    channels = 2
    if FLAGS.scenario == 2:
        channels = 4
    elif FLAGS.scenario == 3:
        channels = 6

    _, _, holdout_set, hand_set = convert_to_tfds(dataset, channels)
    
    def calculate_metrics(model, dataset:tf.data.Dataset):
        TP, FP, TN, FN = 0, 0, 0, 0
        for scene in dataset.as_numpy_iterator():
            img, tgt, _ = scene             # Do not need weights
            logits = model.predict(img)
            pred = tf.argmax(logits, axis=3)
            pred, tgt = np.ravel(pred), np.ravel(tgt)

            for i in range(len(pred)):
                if pred[i] == tgt[i] == 1:
                    TP += 1
                elif pred[i]==1 and tgt[i]!=pred[i]:
                    FP += 1
                elif pred[i] == tgt[i] == 0:
                    TN += 1
                elif pred[i]==0 and tgt[i]!=pred[i]:
                    FN += 1

        water_IoU = TP / (TP + FP + FN)
        water_p = TP / (TP + FP)
        water_r = TP / (TP + FN)
        water_f = (2*water_p * water_r) / (water_p + water_r)

        return  water_IoU, water_p, water_r, water_f

    hand_water_IoU, hand_water_p, hand_water_r, hand_water_f = calculate_metrics(model, hand_set)
    # hold_water_IoU, hold_water_p, hold_water_r, hold_water_f = calculate_metrics(model, holdout_set)

    # print(f'Water IoU:\t\t {100 * hold_water_IoU}:.2f')
    # print(f'Water Precision:\t\t {100 * hold_water_p}:.2f')
    # print(f'Water Recall:\t\t {100 * hold_water_r}:.2f')
    # print(f'Water F1:\t\t {100 * hold_water_f}:.2f')
    print('\n')
    print(f'Water IoU:\t\t {100 * hand_water_IoU}:.2f')
    print(f'Water Precision:\t\t {100 * hand_water_p}:.2f')
    print(f'Water Recall:\t\t {100 * hand_water_r}:.2f')
    print(f'Water F1:\t\t {100 * hand_water_f}:.2f')



if __name__ == "__main__":
    app.run(main)
