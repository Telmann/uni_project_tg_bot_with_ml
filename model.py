import xgboost  # 2.0.3 check

import joblib

# print("XGBoost version", xgboost.__version__)

best_xgb = joblib.load('my_xgb_cv_7_model.pkl')

# xgboost.Booster.load_model(fname='my_xgb_cv_7_model.pkl')

# best_xgb = xgboost.Booster()
# best_xgb.load_model('my_xgb_cv_7_model.pkl')


def model_predict(data):
    y_pred_xgb = best_xgb.predict(data)

    return y_pred_xgb
