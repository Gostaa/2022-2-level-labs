"""
Lab 4
Summarize text using TextRank algorithm
"""
import re
from typing import Union, Any, Tuple, get_args

from lab_3_keywords_textrank.main import TextEncoder, \
    TextPreprocessor, TFIDFAdapter

PreprocessedSentence = tuple[str, ...]
EncodedSentence = tuple[int, ...]


def check_types(value: Any, value_type: type, elements_type: type) -> None:
    """
    Raises ValueError when type is not expected
    :param value:
    :param value_type:
    :param elements_type:
    """
    if not isinstance(value, value_type):
        raise ValueError
    for element in value:
        if not isinstance(element, elements_type):
            raise ValueError


class Sentence:
    """
    An abstraction over the real-world sentences
    """

    def __init__(self, text: str, position: int) -> None:
        """
        Constructs all the necessary attributes
        """
        self.set_text(text)
        if not isinstance(position, int) or isinstance(position, bool):
            raise ValueError

        self._position = position
        self._preprocessed: Tuple[str, ...] = ()
        self._encoded: Tuple[int, ...] = ()

    def get_position(self) -> int:
        """
        Returns the attribute
        :return: the position of the sentence in the text
        """
        return self._position

    def set_text(self, text: str) -> None:
        """
        Sets the attribute
        :param text: the text
        :return: None
        """
        if not isinstance(text, str):
            raise ValueError
        self._text = text

    def get_text(self) -> str:
        """
        Returns the attribute
        :return: the text
        """
        return self._text

    def set_preprocessed(self, preprocessed_sentence: PreprocessedSentence) -> None:
        """
        Sets the attribute
        :param preprocessed_sentence: the preprocessed sentence (a sequence of tokens)
        :return: None
        """
        check_types(preprocessed_sentence, tuple, str)

        self._preprocessed = preprocessed_sentence

    def get_preprocessed(self) -> PreprocessedSentence:
        """
        Returns the attribute
        :return: the preprocessed sentence (a sequence of tokens)
        """
        return self._preprocessed

    def set_encoded(self, encoded_sentence: EncodedSentence) -> None:
        """
        Sets the attribute
        :param encoded_sentence: the encoded sentence (a sequence of numbers)
        :return: None
        """
        check_types(encoded_sentence, tuple, int)

        self._encoded = encoded_sentence

    def get_encoded(self) -> EncodedSentence:
        """
        Returns the attribute
        :return: the encoded sentence (a sequence of numbers)
        """
        return self._encoded


class SentencePreprocessor(TextPreprocessor):
    """
    Class for sentence preprocessing
    """

    def __init__(self, stop_words: tuple[str, ...], punctuation: tuple[str, ...]) -> None:
        """
        Constructs all the necessary attributes
        """
        check_types(stop_words, tuple, str)
        check_types(punctuation, tuple, str)

        super().__init__(stop_words, punctuation)

    def _split_by_sentence(self, text: str) -> tuple[Sentence, ...]:
        """
        Splits the provided text by sentence
        :param text: the raw text
        :return: a sequence of sentences
        """
        if not isinstance(text, str):
            raise ValueError

        text = text.replace('\n', ' ').replace('  ', ' ')
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZА-Я])", text)
        return tuple(Sentence(sentence, position) for position, sentence in enumerate(sentences))

    def _preprocess_sentences(self, sentences: tuple[Sentence, ...]) -> None:
        """
        Enriches the instances of sentences with their preprocessed versions
        :param sentences: a list of sentences
        :return:
        """
        check_types(sentences, tuple, Sentence)

        for sentence in sentences:
            sentence.set_preprocessed(self.preprocess_text(sentence.get_text()))

    def get_sentences(self, text: str) -> tuple[Sentence, ...]:
        """
        Extracts the sentences from the given text & preprocesses them
        :param text: the raw text
        :return:
        """
        sentences = self._split_by_sentence(text)
        self._preprocess_sentences(sentences)
        return sentences


class SentenceEncoder(TextEncoder):
    """
    A class to encode string sequence into matching integer sequence
    """

    def __init__(self) -> None:
        """
        Constructs all the necessary attributes
        """
        super().__init__()
        self._last_idx = 1000

    def _learn_indices(self, tokens: tuple[str, ...]) -> None:
        """
        Fills attributes mapping words and integer equivalents to each other
        :param tokens: a sequence of string tokens
        :return:
        """
        check_types(tokens, tuple, str)

        for word in set(tokens):
            if word in self._word2id:
                continue
            self._word2id[word] = self._last_idx
            self._id2word[self._last_idx] = word
            self._last_idx += 1

    def encode_sentences(self, sentences: tuple[Sentence, ...]) -> None:
        """
        Enriches the instances of sentences with their encoded versions
        :param sentences: a sequence of sentences
        :return: a list of sentences with their preprocessed versions
        """
        check_types(sentences, tuple, Sentence)

        for sentence in sentences:
            self._learn_indices(sentence.get_preprocessed())
            sentence.set_encoded(tuple(self._word2id[word] for word in sentence.get_preprocessed()))


def calculate_similarity(sequence: Union[list, tuple], other_sequence: Union[list, tuple]) -> float:
    """
    Calculates similarity between two sequences using Jaccard index
    :param sequence: a sequence of items
    :param other_sequence: a sequence of items
    :return: similarity score
    """
    if not isinstance(sequence, get_args(Union[list, tuple])) or not isinstance(other_sequence,
                                                                                get_args(Union[list, tuple])):
        raise ValueError
    if not sequence and not other_sequence:
        return 0
    sequence_set = set(sequence)
    other_sequence_set = set(other_sequence)
    return len(sequence_set.intersection(other_sequence_set)) / len(sequence_set.union(other_sequence_set))


class SimilarityMatrix:
    """
    A class to represent relations between sentences
    """

    _matrix: list[list[float]]
    _vertices: list[Sentence]

    def __init__(self) -> None:
        """
        Constructs necessary attributes
        """
        self._matrix = []
        self._vertices = []

    def get_vertices(self) -> tuple[Sentence, ...]:
        """
        Returns a sequence of all vertices present in the graph
        :return: a sequence of vertices
        """
        return tuple(self._vertices)

    def calculate_inout_score(self, vertex: Sentence) -> int:
        """
        Retrieves a number of vertices that are similar (i.e. have similarity score > 0) to the input one
        :param vertex
        :return:
        """
        if vertex not in self._vertices:
            raise ValueError
        idx = self._vertices.index(vertex)
        return sum(1 for score in self._matrix[idx] if score > 0)

    def add_edge(self, vertex1: Sentence, vertex2: Sentence) -> None:
        """
        Adds or overwrites an edge in the graph between the specified vertices
        :param vertex1:
        :param vertex2:
        :return:
        """
        if not isinstance(vertex1, Sentence) or not isinstance(vertex2, Sentence):
            raise ValueError

        if vertex1 == vertex2:
            raise ValueError
        for vertex in vertex1, vertex2:
            if vertex not in self._vertices:
                self._vertices.append(vertex)
                self._matrix.append([])

        for edges_list in self._matrix:
            if len(edges_list) < len(self._vertices):
                edges_list.extend([0 for _ in range(len(self._vertices) - len(edges_list))])

        idx1 = self._vertices.index(vertex1)
        idx2 = self._vertices.index(vertex2)
        jaccard_index = calculate_similarity(vertex1.get_encoded(), vertex2.get_encoded())
        self._matrix[idx1][idx2] = jaccard_index
        self._matrix[idx2][idx1] = jaccard_index

    def get_similarity_score(self, sentence: Sentence, other_sentence: Sentence) -> float:
        """
        Gets the similarity score for two sentences from the matrix
        :param sentence
        :param other_sentence
        :return: the similarity score
        """
        if sentence not in self._vertices or other_sentence not in self._vertices:
            raise ValueError
        idx1 = self._vertices.index(sentence)
        idx2 = self._vertices.index(other_sentence)
        return self._matrix[idx1][idx2]

    def fill_from_sentences(self, sentences: tuple[Sentence, ...]) -> None:
        """
        Updates graph instance with vertices and edges extracted from sentences
        :param sentences
        :return:
        """
        if not isinstance(sentences, tuple) or not sentences:
            raise ValueError

        for sentence in sentences:
            for other_sentence in sentences:
                if sentence.get_encoded() != other_sentence.get_encoded():
                    self.add_edge(sentence, other_sentence)



class TextRankSummarizer:
    """
    TextRank for summarization
    """

    _scores: dict[Sentence, float]
    _graph: SimilarityMatrix

    def __init__(self, graph: SimilarityMatrix) -> None:
        """
        Constructs all the necessary attributes
        :param graph: the filled instance of the similarity matrix
        """
        if not isinstance(graph, SimilarityMatrix):
            raise ValueError
        self._graph = graph
        self._damping_factor = 0.85
        self._convergence_threshold = 0.0001
        self._max_iter = 50
        self._scores = {}

    def update_vertex_score(
            self, vertex: Sentence, incidental_vertices: list[Sentence], scores: dict[Sentence, float]
    ) -> None:
        """
        Changes vertex significance score using algorithm-specific formula
        :param vertex: a sentence
        :param incidental_vertices: vertices with similarity score > 0 for vertex
        :param scores: current vertices scores
        :return:
        """
        summary = sum((1 / self._graph.calculate_inout_score(inc_vertex)) * scores[inc_vertex]
                      for inc_vertex in incidental_vertices)
        self._scores[vertex] = summary * self._damping_factor + (1 - self._damping_factor)

    def train(self) -> None:
        """
        Iteratively computes significance scores for vertices
        """
        vertices = self._graph.get_vertices()
        for vertex in vertices:
            self._scores[vertex] = 1.0

        for iteration in range(self._max_iter):
            prev_score = self._scores.copy()
            for scored_vertex in vertices:
                similar_vertices = [vertex for vertex in vertices
                                    if self._graph.get_similarity_score(scored_vertex, vertex) > 0]
                self.update_vertex_score(scored_vertex, similar_vertices, prev_score)
            abs_score_diff = [abs(i - j) for i, j in zip(prev_score.values(), self._scores.values())]

            if sum(abs_score_diff) <= self._convergence_threshold:  # convergence condition
                print("Converging at iteration " + str(iteration) + "...")
                break

    def get_top_sentences(self, n_sentences: int) -> tuple[Sentence, ...]:
        """
        Retrieves top n most important sentences in the encoded text
        :param n_sentences: number of sentence to retrieve
        :return: a sequence of sentences
        """
        if not n_sentences or not isinstance(n_sentences, int) or isinstance(n_sentences, bool):
            raise ValueError
        sorted_sentences = sorted(self._scores, key=lambda sentence: self._scores[sentence], reverse=True)
        return tuple(sentence for sentence in sorted_sentences)[:n_sentences]

    def make_summary(self, n_sentences: int) -> str:
        """
        Constructs summary from the most important sentences
        :param n_sentences: number of sentences to include in the summary
        :return: summary
        """
        top = sorted(self.get_top_sentences(n_sentences), key=lambda sentence: sentence.get_position())
        return '\n'.join(sentence.get_text() for sentence in top)


class NoRelevantTextsError(Exception):
    pass


class IncorrectQueryError(Exception):
    pass


class Buddy:
    """
    (Almost) All-knowing entity
    """

    def __init__(
            self,
            paths_to_texts: list[str],
            stop_words: tuple[str, ...],
            punctuation: tuple[str, ...],
            idf_values: dict[str, float],
    ):
        """
        Constructs all the necessary attributes
        :param paths_to_texts: paths to the texts from which to learn
        :param stop_words: a sequence of stop words
        :param punctuation: a sequence of punctuation symbols
        :param idf_values: pre-computed IDF values
        """
        self._stop_words = stop_words
        self._punctuation = punctuation
        self._idf_values = idf_values
        self._text_preprocessor = TextPreprocessor(stop_words, punctuation)
        self._sentence_encoder = SentenceEncoder()
        self._sentence_preprocessor = SentencePreprocessor(stop_words, punctuation)
        self._knowledge_database = {}
        self._paths_to_texts = paths_to_texts

        for path in paths_to_texts:
            self.add_text_to_database(path)

    def add_text_to_database(self, path_to_text: str) -> None:
        """
        Adds the given text to the existing database
        :param path_to_text
        :return:
        """
        if not path_to_text or not isinstance(path_to_text, str):
            raise ValueError

        with open(path_to_text, 'r', encoding='utf-8') as file:
            text = file.read()

        sentence_preprocessor = SentencePreprocessor(self._stop_words, self._punctuation)
        sentences = sentence_preprocessor.get_sentences(text)
        self._sentence_encoder.encode_sentences(sentences)

        tokens = self._text_preprocessor.preprocess_text(text)
        tfidf_adapter = TFIDFAdapter(tokens, self._idf_values)
        tfidf_adapter.train()
        top_keywords = tfidf_adapter.get_top_keywords(100)

        graph = SimilarityMatrix()
        graph.fill_from_sentences(sentences)

        summarizer = TextRankSummarizer(graph)
        summarizer.train()
        summary = summarizer.make_summary(5)

        self._knowledge_database[path_to_text] = {
            'sentences': sentences,
            'keywords': top_keywords,
            'summary': summary
        }

    def _find_texts_close_to_keywords(self, keywords: tuple[str, ...], n_texts: int) -> tuple[str, ...]:
        """
        Finds texts that are similar (i.e. contain the same keywords) to the given keywords
        :param keywords: a sequence of keywords
        :param n_texts: number of texts to find
        :return: the texts' ids
        """
        if not keywords or not n_texts or isinstance(n_texts, bool) or not isinstance(n_texts, int):
            raise ValueError
        check_types(keywords, tuple, str)

        similarities = {}
        for path, value in self._knowledge_database.items():
            similarities[path] = calculate_similarity(keywords, value['keywords'])
        if sum(similarities.values()) == 0:
            raise NoRelevantTextsError('Texts that are related to the query were not found. Try another query.')
        return tuple(sorted(similarities, key=lambda path: (similarities[path], path), reverse=True)[:n_texts])

    def reply(self, query: str, n_summaries: int = 3) -> str:
        """
        Replies to the query
        :param query: the query
        :param n_summaries: the number of summaries to include in the answer
        :return: the answer
        """
        if not isinstance(n_summaries, int) or isinstance(n_summaries, bool):
            raise ValueError
        if len(self._knowledge_database) < n_summaries:
            raise ValueError
        if not isinstance(query, str) or not query:
            raise IncorrectQueryError('Incorrect query. Use string as input.')

        keywords = self._text_preprocessor.preprocess_text(query)
        closest_texts = self._find_texts_close_to_keywords(keywords, n_summaries)
        summaries = [self._knowledge_database[text]['summary'] for text in closest_texts]
        return 'Ответ:\n' + '\n\n'.join(summaries)
