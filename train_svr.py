import os
import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from scipy.stats import spearmanr, pearsonr
import joblib
import config

# 特征目录
FEATURE_DIR = r"F:\毕业设计\data\features"

# 读取MOS文件
mos_data = pd.read_csv(config.MOS_FILE)

# 建立字典方便查找MOS
mos_dict = dict(zip(mos_data.iloc[:,0].astype(str), mos_data.iloc[:,1]))

X = []
y = []

# 遍历features文件夹
for file in os.listdir(FEATURE_DIR):

    if file.endswith(".npy"):

        video_name = os.path.splitext(file)[0]

        # 判断MOS是否存在
        if video_name in mos_dict:

            feature_path = os.path.join(FEATURE_DIR, file)

            feat = np.load(feature_path)

            # 如果是多帧特征 -> 做平均池化
            if len(feat.shape) > 1:
                feat = np.mean(feat, axis=0)

            X.append(feat)
            y.append(mos_dict[video_name])

            print("Loaded:", file)

X = np.array(X)
y = np.array(y)

print("Feature shape:", X.shape)
print("Label shape:", y.shape)

# 划分训练测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 特征标准化
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# SVR模型
model = SVR(kernel="rbf", C=10, gamma="scale")

model.fit(X_train, y_train)

# 预测
pred = model.predict(X_test)

# 评价指标
mse = mean_squared_error(y_test, pred)
rmse = np.sqrt(mse)
plcc = pearsonr(y_test, pred)[0]
srcc = spearmanr(y_test, pred)[0]

print("RMSE:", rmse)
print("PLCC:", plcc)
print("SRCC:", srcc)

# 保存模型
joblib.dump(model, "svr_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("Model saved.")