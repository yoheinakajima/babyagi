import openai



def get_ada_embedding(text: str) :
        """
        Generate an ADA text embedding.

        :param text: Input text for embedding.
        :return: List of floats as ADA text embedding.
        """
        text = text.replace("\n", " ")
        return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]