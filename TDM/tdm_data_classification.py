import random
import json
from textwrap import indent
import pandas as pd
from datetime import datetime
from faker import Faker
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import numpy as np
starttime = datetime.now()
# Initialize Faker
fake = Faker()
tdm_config = []

# Custom feature extractor
class TextStats(BaseEstimator, TransformerMixin):
    def fit(self, x, y=None):
        return self

    def transform(self, texts):
        features = []
        for text in texts:
            features.append([
                int(any(char.isdigit() for char in text)),     # has_digit
                int("@" in text),                              # has_at
                int(".com" in text or ".org" in text or ".net" in text), # has_domain
                int("+" in text),                              # has_plus
                int(len(text.split())),                        # num_words
                int(text[0].isupper()),                        # starts_with_cap
                int("," in text),                              # contains_comma
                int("(" in text or ")" in text),               # has_parentheses
                int("-" in text),                              # has_dash
            ])
        return np.array(features)

# Generate data
samples_per_class = 500
data, labels = [], []

# FIRST_NAME
for _ in range(samples_per_class):
    data.append(fake.first_name())
    labels.append("FIRST_NAME")

# FULL_NAME
full_name_variants = [
    "Ada Lovelace", "Elon Musk", "Alan Turing", "Grace Hopper", "Tim Berners-Lee"
]
for _ in range(samples_per_class):
    choice = random.choice([
        fake.name(),
        "Dr. " + fake.name(),
        fake.first_name() + " " + fake.last_name() + " Jr.",
        fake.first_name()[0] + ". " + fake.last_name(),
        random.choice(full_name_variants)
    ])
    data.append(choice)
    labels.append("FULL_NAME")

# ADDRESS
address_variants = [
    "123 Main St", "10 Pine Rd", "5 Oak Blvd", "1 Elm St", "221B Baker Street"
]
for _ in range(samples_per_class):
    choice = random.choice([
        fake.address().replace("\n", " "),
        fake.street_address(),
        fake.building_number() + " " + fake.street_name(),
        fake.secondary_address(),
        random.choice(address_variants)
    ])
    data.append(choice)
    labels.append("ADDRESS")

# EMAIL
email_variants = [
    "test.user+spam@example.co.uk", "info@company.io", "john_doe@sub.domain.com"
]
for _ in range(samples_per_class):
    choice = random.choice([
        fake.email(),
        random.choice(email_variants)
    ])
    data.append(choice)
    labels.append("EMAIL")

# PHONE_NUMBER
for _ in range(samples_per_class):
    choice = random.choice([
        fake.phone_number(),
        fake.msisdn(),
        "+1 " + fake.msisdn(),
        "(123) 456-7890",
        "+44 20 7946 0958"
    ])
    data.append(choice)
    labels.append("PHONE_NUMBER")

#DATE
for _ in range(samples_per_class):
    choice = random.choice([
        fake.date()
    ])
    data.append(str(choice))
    labels.append("DATE")

#DATETIME
for _ in range(samples_per_class):
    choice = random.choice([
        fake.date_time()
    ])
    data.append(str(choice))
    labels.append("DATE_TIME")

#time
for _ in range(samples_per_class):
    _hour = random.randint(0,23)
    _minute = random.randint(0, 59)
    _second = random.randint(0, 59)
    time= f"{_hour:02d}:{_minute:02d}:{_second:02d}"
    data.append(time)
    labels.append("TIME")


#integers
for _ in range(samples_per_class):
    choice = random.choice([
        random.randint(0,100000000000000)
    ])
    data.append(str(choice))
    labels.append("NUMBER-INT")
#decimals
for _ in range(samples_per_class):
    choice = random.choice([
        random.uniform(0.0,100000000000000.0)
    ])
    data.append(str(choice))
    labels.append("NUMBER-DECIMAL")

#binary
for _ in range(samples_per_class):
    binary_data = fake.binary(32)  # 32 bytes of binary data
    hex_value = hex(int(binary_data.hex(), 16))  # Convert to hex string
    data.append(hex_value)
    labels.append("BINARY")

#list


for _ in range(samples_per_class):
    list_sample = random.choice([
        [fake.first_name(), fake.first_name(), fake.first_name()],
        [fake.email(), fake.email()],
        ["active", "inactive", "pending"],
        ["yes", "no"],
        ["red", "green", "blue"]
    ])
    data.append(" | ".join(list_sample))  # Match format used in prediction
    labels.append("LIST")



# OTHER
for _ in range(samples_per_class):
    choice = random.choice([
        fake.sentence(nb_words=random.randint(3, 8)),
        fake.bs(),
        fake.catch_phrase(),
        fake.company(),
        fake.text(max_nb_chars=30),
        "This is just some random unstructured text.",
        "Example of unrelated content.",
        "This string shouldn't match anything."
    ])
    data.append(choice)
    labels.append("OTHER")

# Shuffle
combined = list(zip(data, labels))
random.shuffle(combined)
data[:], labels[:] = zip(*combined)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.3, random_state=42)

# Pipeline with TF-IDF + Custom Features
model = Pipeline([
    ('features', FeatureUnion([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 6))),
        ('textstats', TextStats())
    ])),
    ('clf', LogisticRegression(max_iter=500, C=0.5))
])

# Train
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("Classification Report:\n")
print(classification_report(y_test, y_pred))

# ---- Test Predictions ----
csv_file_path = 'C:/Users/antonim/Downloads/samples_tdm_config.csv'
df = pd.read_csv(csv_file_path)


# Dictionary to store predictions for each column
column_predictions = {}

# Iterate over each column and predict the datatype
for column in df.columns:
    column_data = df[column].dropna().astype(str).tolist()  # Convert to string and drop NaN
    predictions = model.predict(column_data)

    # Adjust predictions for numbers
    adjusted_predictions = []
    for text, prediction in zip(column_data, predictions):
        # Check if the prediction is NUMBER-DECIMAL but the text is actually an integer
        if prediction == "NUMBER-DECIMAL" and text.isdigit():
            prediction = "NUMBER-INT"
        adjusted_predictions.append(prediction)


    # Count the most frequent prediction for the column
    most_common_prediction = max(set(adjusted_predictions), key=adjusted_predictions.count)
    column_predictions[column] = most_common_prediction
    print(f"Column '{column}' is predicted as: {most_common_prediction}")

print("its running")
for column, prediction in column_predictions.items():
    if prediction == "FULL_NAME":
        tdm_config.append({
            "name": column,
            "type": "person-name",
        })
    elif prediction == "FIRST_NAME":
        tdm_config.append({
            "name": column,
            "type": "first_name",
        })
    elif prediction == "ADDRESS":
        tdm_config.append({
            "name": column,
            "type": "ca-address"
        })
    elif prediction == "NUMBER-INT":
        tdm_config.append({
            "name": column,
            "type": "number-int"
        })
    elif prediction == "NUMBER-DECIMAL":
        tdm_config.append({
            "name": column,
            "type": "number-decimal"
        })
    elif prediction == "EMAIL":
        tdm_config.append({
            "name": column,
            "type": "email"
        })
    elif prediction == "BINARY":
        tdm_config.append({
            "name": column,
            "type": "binary"
        })
    elif prediction == "TIME":
        tdm_config.append({
            "name": column,
            "type": "time"
        })
    elif prediction == "PHONE_NUMBER":
        tdm_config.append({
            "name": column,
            "type": "phonenumber"
        })
    elif prediction == "LIST":
        tdm_config.append({
            "name": column,
            "type": "list"
        })
    else:
        tdm_config.append({
            "name": column,
            "type": "other"
        })

# Create the test data configuration
test_data_config = {
    "table_name": {  # Name of the table you're working with
    "records": 100,  # Number of records to be processed or generated
    "preprocessing": [],  # Any preprocessing steps (currently empty)
    "cols": tdm_config,
    "postprocessing": [
        {
                "name": "createview",
                "type":"createview",
                "tablename": "table_name"
            }
    ]
}
}
print("test_data_config = ")
tdm_config_json = json.dumps(test_data_config, indent=4)
print(tdm_config_json)

endtime = datetime.now()
timetaken = endtime - starttime
print("time taken", timetaken)
