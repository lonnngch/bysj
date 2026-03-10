from scipy.stats import spearmanr, pearsonr
import numpy as np

def compute_metrics(preds,labels):

    preds = np.array(preds)
    labels = np.array(labels)

    plcc = pearsonr(preds,labels)[0]
    srcc = spearmanr(preds,labels)[0]

    return plcc,srcc