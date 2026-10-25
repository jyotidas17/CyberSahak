# SMS Spam training data

`sms_spam_collection.tsv` is the UCI SMS Spam Collection, fetched with the UCI Machine Learning Repository client (`ucimlrepo.fetch_ucirepo(id=228)`). It contains 5,574 labeled messages (`ham`/`spam`) and is licensed CC BY 4.0.

Attribution: Tiago Almeida and José Hidalgo, “SMS Spam Collection,” UCI Machine Learning Repository, DOI [10.24432/C5CC84](https://doi.org/10.24432/C5CC84).

This is general SMS spam data, not a representative Indian phishing dataset. CyberSahak uses the model only as a supplementary spam-like indicator; the existing explainable rules remain primary. The model must not be described as proof that a message is fraudulent.
