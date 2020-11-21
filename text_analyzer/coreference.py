# Load your usual SpaCy model (one of SpaCy English models)
import spacy
import neuralcoref

class Coref:
    def __init__(self):
        self.nlp = spacy.load('en')

        # Add neural coref to SpaCy's pipe
        neuralcoref.add_to_pipe(self.nlp)

    def __call__(self, text):
        # You're done. You can now use NeuralCoref as you usually manipulate a SpaCy document annotations.
        doc = self.nlp(text)
        return doc._.coref_resolved


if __name__ == "__main__":
    coref = Coref()
    print(coref('My sister has a dog. She loves him.'))
