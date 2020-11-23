import tensorflow_hub as hub
from numpy import dot
from numpy.linalg import norm

embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")


def cos_sim(A, B):
    # 코사인 유사도
    return dot(A, B)/(norm(A)*norm(B))


def comp_with(main, sentences):
    # main과 sentences의 문장을 비교한다.
    if not isinstance(main, str):
        raise TypeError("`main` must be a str type.")
    if not isinstance(sentences, list):
        sentences = [sentences]

    embeddings = embed([main] + sentences)
    main_emb = embeddings[0]
    sene_emb = embeddings[1:]

    result = [(cos_sim(embedding, main_emb), sen) for embedding, sen in zip(sene_emb, sentences)]
    return result


if __name__ == "__main__":
    sentences = [
        "dokdo is japanese territory",
        "dokdo is island of korea"
    ]

    print(comp_with('dokdo is korean territory', sentences))
