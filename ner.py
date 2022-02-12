# noinspection LanguageDetectionInspection
import re
import os
import io
import itertools
import json
from natasha import NamesExtractor, MorphVocab, Doc, Segmenter, NewsEmbedding, NewsNERTagger
import logging
import regex_patterns

logger = logging.getLogger()
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)-15s %(levelname)s %(funcName)s %(message)s"
)

morph_vocab = MorphVocab()
segmenter = Segmenter()
names_extractor = NamesExtractor(morph_vocab)
emb = NewsEmbedding()
ner_tagger = NewsNERTagger(emb)


def extract_name_from_db_field(text_field: str):
    """ full_case.u_common_case_defendant_m Field example:
    Габдуллин Р.Ф..  ...  .01.09.2015.  ...  .ст.228 ч.1 УК РФ.  ...  .ОБВИНИТЕЛЬНЫЙ приговор
    """
    if text_field is None:
        return None
    results = []
    doc = Doc(text_field)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)
    for s in doc.spans:
        if s.type == "PER":
            results.append(s.text)
    if len(results) == 0:
        return None
    return results


def extract_articles(case_document_articles_record: str):
    parts = case_document_articles_record[2:-2].split('", "')

    # DIfferent Split cases
    parts = list(itertools.chain(*[p.split("] [") for p in parts]))
    parts = list(itertools.chain(*[p.split("; ") for p in parts]))
    parts = [
        p.replace(". ", ".")
        .replace(" - ", ", ")
        .replace("[", "")
        .replace("]", "")
        .replace("-", ", ")
        for p in parts
    ]
    return parts


class EntityExtractor:
    intro_limit = 200  # first symbols to search for sentence_date

    def __init__(self):
        pass

    @staticmethod
    def split_sentences(text: str):
        doc = Doc(text.replace("\n", " "))
        doc.segment(segmenter)
        sentences = [d.text for d in doc.sents]
        return sentences

    @staticmethod
    def get_court_name(text: str):
        """Суд, выносящий приговор"""
        try:
            match = regex_patterns.court_name_pattern.search(text)
            return match.group(1)
        except BaseException as e:
            error_msg = "Could not extract court_name"
            logger.error(error_msg)

    @staticmethod
    def get_defendants(text: str):
        """Фио подсудимых"""
        # defendants list
        defendants = []

        try:
            # search for pattern in text
            match = regex_patterns.defendant_full_name_pattern.search(text)

            # parse line with NamesExtractor
            name = ner_tagger(match.group(0).strip(", -\t\r\n"))

            # if there are name matches
            if len(name.matches) > 0:

                # get names as json
                defendant_dict = name.matches[0].fact.as_json

                # if there is surname
                if "last" in defendant_dict:
                    # uppercase first letter
                    defendant_dict["last"] = (
                        defendant_dict["last"][0].upper() + defendant_dict["last"][1:]
                    )

                    # create full name, if part (last/first/middle/) is not found, dict.get(key) returns None
                    last = defendant_dict.get("last")
                    first = defendant_dict.get("first")
                    middle = defendant_dict.get("middle")
                    full_name = "{} {}.{}".format(last, first, middle)
                    defendants.append(full_name)

                # if there are no matches
                else:
                    # add regexp match to dict
                    defendants.append(match.group(1).strip(", -\t\r\n"))

            # if there are no matches
            else:
                # add regexp match to dict
                return None
        except BaseException as e:
            err_msg = "Could not extract defendatns: {}".format(e)
            logger.warning(err_msg)

        # return defendants list
        return ", ".join(defendants)

    @staticmethod
    def get_conviction(text: str):
        """ Судимость да/нет """
        result = None
        try:
            for p in regex_patterns.non_conviction_patterns:
                if p in text:
                    result = False
            for p in regex_patterns.conviction_patterns:
                if p in text:
                    result = True
            return result
            
        except BaseException as e:
            err_msg = "Could not extract conviction: {}".format(e)
            logger.warning(err_msg)

    @staticmethod
    def get_imprisonment(text: str):
        """Отбывал ли ранее лишение свободы да/нет"""

        try:
            # iterate all imprisonment patterns
            for pattern in regex_patterns.imprisonment_patterns:
                # if matches, then there was imprisonment
                if pattern.search(text) != None:
                    return True
        except BaseException as e:
            err_msg = "Could not extract imprisonment: {}".format(e)
            logger.warning(err_msg)

    @staticmethod
    def get_drugs(text: str):
        """Словарь {Вид наркотика: количество}"""
        drugs = {}
        for pattern in regex_patterns.drugs_mass_patterns:
            # search for all drug mass patterns
            matches = pattern.findall(text)
            if matches:
                for match in matches:
                    name = None
                    try:
                        name = next(
                            drug_pattern
                            for drug_pattern in regex_patterns.drugs_sizes.keys()
                            if re.search(r"\b" + drug_pattern + r"\b", match[0])
                        )
                    except:
                        try:
                            name = next(
                                regex_patterns.special_regex_cases[drug_pattern]
                                for drug_pattern in regex_patterns.special_regex_cases.keys()
                                if re.search(drug_pattern, match[0])
                            )
                        except:
                            name = None
                    finally:
                        if name is not None:
                            # correct name
                            if name == "является производным":
                                name = "производное"
                            # add drug to dict
                            if name not in drugs:
                                drugs[name] = match[1] + " " + match[2]

        # if there were no matches
        if not drugs:
            name = None
            # find drug patterns in the whole text
            try:
                name = next(
                    drug_pattern
                    for drug_pattern in regex_patterns.drugs_sizes.keys()
                    if re.search(r"\b" + drug_pattern + r"\b", text)
                )
            except:
                name = next(
                    regex_patterns.special_regex_cases[drug_pattern]
                    for drug_pattern in regex_patterns.special_regex_cases.keys()
                    if re.search(drug_pattern, text)
                )

                # add drug to dict
                drugs[name] = None

            # if no drug found
            finally:
                if name is not None:
                    if name == "является производным":
                        name = "производное"
                err_msg = "No drugs found in whole text, check matches: {}".format(
                    matches
                )
                logger.warning(err_msg)
                return None

        # TODO: move to self.normalize_values() with dict type check
        drug_string = "; ".join(
            k + ": " + EntityExtractor.normalize_value(v) for k, v in drugs.items()
        )
        return drug_string

    @staticmethod
    def get_largest_drug(text: str, drugs: str):
        """Выделение самого крупного по относительному размеру наркотика"""

        # строка со списком наркотиков, в рефакторинге можно перенести в метод drugs
        if drugs is None:
            return None

        drugs_pairs = drugs.split("; ")
        just_names = []

        # найденные массы наркотиков
        drugs = {}
        largest_drug = ""

        for pair in drugs_pairs:
            try:
                drug, size = pair.split(":")
                just_names.append(drug)
                mass = size.split()[0].strip()
                mass = mass.replace(" ", "")
                mass = mass.replace(",", ".")

                drugs[drug] = float(mass)

            except:
                pass

        # сюда запишем размеры наркотиков относительно интервалов крупности размеров
        found_sizes = {}

        for drug_name, drug_mass in drugs.items():

            if drug_mass > 0:

                # из словарика размеров получаем лист [значительный, крупный, особо крупный]
                if drug_name in regex_patterns.drugs_sizes:
                    sizes_list = regex_patterns.drugs_sizes[drug_name]

                elif drug_name in regex_patterns.special_regex_sizes:
                    sizes_list = regex_patterns.special_regex_sizes[drug_name]

                else:
                    continue

                # значительный - какая часть от крупного, принимает значения (0 - 1)
                if drug_mass < sizes_list[1]:
                    found_sizes[drug_name] = drug_mass / sizes_list[1]

                # особо крупный - во сколько раз больше крупного + 2, чтобы было больше всего, принимает значения  > 2
                elif drug_mass >= sizes_list[2]:
                    found_sizes[drug_name] = 1 + drug_mass / sizes_list[2]

                # крупный - какая часть от особо крупного + 1, чтобы было больше значительного, принимает значения  (1 - 2)
                else:
                    found_sizes[drug_name] = 1 + drug_mass / sizes_list[2]

        if len(found_sizes) > 0:
            largest_drug = max(found_sizes, key=lambda x: found_sizes[x])
        else:
            # если ничего не нашли, то перечисляем все через ;
            largest_drug = "; ".join(just_names)

        return largest_drug

    @staticmethod
    def get_general_drug_size(text: str):
        """Ищет наибольший размер (особо крупный -> крупный -> значительный), указанный в тексте приговора"""
        for drug_size_title, drug_size in regex_patterns.general_drug_size_patterns.items():
            if drug_size in text:
                return drug_size_title
        return None

    @staticmethod
    def get_punishment(text: str):
        """Вид наказания (лишение свободы/ условное лишение свободы) и срок"""

        # zero results
        punishment_type = ""
        punishment_duration = 0

        sentence_match = regex_patterns.sentence_patterns.search(text)

        # if there is no sentence pattern
        if sentence_match == None:
            return None, None

        # get type of sentence - suspended or not
        punishment_type = (
            "Условное лишение свободы"
            if all(e in text[sentence_match.start():] for e in regex_patterns.suspended_sentence_patterns               )
            else "Лишение свободы"
        )

        # years and months
        years = 0
        months = 0

        # iterate all punishment patterns
        for i in range(len(regex_patterns.punishment_patterns)):

            # search punishment
            punishment_match = regex_patterns.punishment_patterns[i].search(
                text[sentence_match.start():]
            )

            # if there is match
            if punishment_match is None:
                return punishment_type, None
            else:

                # check for exceptions
                try:

                    # check for first group prescense
                    if len(punishment_match.groups()) == 0:
                        continue

                    # get years
                    years = (
                        int(punishment_match.group(1))
                        if i == 1
                        else regex_patterns.russian_numbers.index(
                            punishment_match.group(1).lower()
                        )
                    )

                    # if second group exist
                    if punishment_match.group(2) != None:

                        # get months
                        months = (
                            int(punishment_match.group(2))
                            if i == 1
                            else regex_patterns.russian_numbers.index(
                                punishment_match.group(2).lower()
                            )
                        )

                    # print(punishment_match.group(0))
                    # print("Years: ", years)
                    # print("Months: ", months)

                    # set punishment duration
                    punishment_duration_month = years * 12 + months
                    break

                # continue in case of exception
                except:
                    continue

        # return type and duration
        return punishment_type, punishment_duration_month

    @staticmethod
    def get_extenuating_circumstances(text: str):
        """Смягчающие обстоятельства"""
        try:
            # iterate all extenuating patterns
            for pattern in regex_patterns.extenuating_patterns:

                # match pattern
                match = pattern.search(text)

                # if there is match
                if match != None and len(match.groups()) > 0:

                    # return first match
                    return match.group(1).strip(" \r\n,.")
        except BaseException as e:
            err_msg = "Could not extract extenuating_circumstances: {}".format(e)
            logger.warning(err_msg)

    @staticmethod
    def get_special_order(text: str):
        """Особый порядок да/нет"""
        return any(e in text for e in regex_patterns.special_order_patterns)

    @staticmethod
    def get_mass(text: str, drugs: str, largest_drug: str):
        main_drug = regex_patterns.drug_clean_dict.get(largest_drug)

        if drugs is None:
            return None

        pairs = drugs.split(";")

        for pair in pairs:
            drug, val = pair.split(":")
            val = val.replace(",", ".").strip()
            mass = re.search(r"((\d)*\.(\d*)?|\d* )", val).group(0)
            try:
                return mass, float(mass)
            except:
                print(f"Could noto conver drug mass to float: {mass}")
                return None

    @staticmethod
    def extract_features(self, text: str):
        # text = text.lower()
        self.text = text

        self.sentences = self.split_sentences(text)

        self.conviction = self.get_conviction(text)
        if not self.conviction:  # TODO: if not convicted before, then there was no imprisonment
            self.imprisonment = False

        self.punishment_type, self.punishment_duration_month = self.get_punishment(self.text)

        self.drugs = self.get_drugs(self.text)
        self.largest_drug = self.get_largest_drug(text, self.drugs)
        self.mass = self.get_mass(text=text, drugs=self.drugs, largest_drug=self.largest_drug)
        summary_dict = {
            "Суд": self.court_name,
            # "Дата приговора": self.sentence_date,
            # "ФИО": self.defendants,
            "Особый порядок": self.special_order,
            "Судимость": self.conviction,
            "Вид наказания": self.punishment_type,
            "Срок наказания в месяцах": self.punishment_duration_month,
            "Отбывал ли ранее лишение свободы": self.imprisonment,
            "Наркотики": self.drugs,
            "Главный наркотик": self.drug_clean_dict.get(self.largest_drug),
            "Размер": self.general_drug_size,
            "Смягчающие обстоятельства": self.extenuating_circumstances,
            "Отягчающие обстоятельства": self.aggravating_circumstances,
            "Количество": self.mass,
        }
        # summary_dict_normalized = {k: self.normalize_value(v) for k, v in summary_dict.items()}
        return summary_dict
