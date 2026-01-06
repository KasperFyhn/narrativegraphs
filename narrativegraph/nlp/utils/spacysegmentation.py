from spacy import Language


@Language.component("custom_sentencizer")
def custom_sentencizer(doc):
    for i, token in enumerate(doc[:-1]):
        if token.text == "\n\n":
            doc[i + 1].is_sent_start = True

    return doc
