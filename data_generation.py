from sdv.metadata import SingleTableMetadata
from sdv.single_table import GaussianCopulaSynthesizer
import pandas as pd

# Загрузка данных
df = pd.read_csv('dataset/volve_field_data_en.csv')

# Обучение модели

# Создание метаданных (автоматическое определение)
metadata = SingleTableMetadata()
metadata.detect_from_dataframe(df)

model = GaussianCopulaSynthesizer(metadata)
model.fit(df)

# Генерация 30 новых записей
new_data = model.sample(30)
new_data.to_csv('dataset/synthetic_data.csv', index=False)
