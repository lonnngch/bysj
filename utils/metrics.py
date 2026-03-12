from scipy.stats import spearmanr, pearsonr
import numpy as np


def compute_metrics(preds, labels):

    preds = np.array(preds)
    labels = np.array(labels)

    srcc = spearmanr(preds, labels)[0]
    plcc = pearsonr(preds, labels)[0]
    rmse = np.sqrt(((preds - labels) ** 2).mean())

    return srcc, plcc, rmse