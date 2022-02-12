import re
import os
import io
import json


class NameParser:
    # patterns to check if pleaded not guilty
    re_plea_not_guilty = [
        re.compile("вину.{0,300}не признал",    re.IGNORECASE),
        re.compile("не признал.{0,300}вину",    re.IGNORECASE),
        re.compile("виновн.{0,300}не признал",  re.IGNORECASE),
        re.compile("не признал.{0,300}виновн",  re.IGNORECASE)]

    # patterns to check if pleaded guilty
    re_plea_guilty = [
        re.compile("вину.{0,300}признал",   re.IGNORECASE),
        re.compile("признал.{0,300}вину",   re.IGNORECASE),
        re.compile("виновн.{0,300}признал", re.IGNORECASE),
        re.compile("признал.{0,300}виновн", re.IGNORECASE),
        re.compile("признание вины",        re.IGNORECASE)]

    # patterns to check if male
    re_male = ["судимого", "имеющего судимость", "признал[\W]"]

    # patterns to check if female
    re_female = ["судимой", "имеющей судимость", "признала"]

    def __init__(self, text: str):
        self.text = text
        self.paragraphs = self.text.split('\n')

    @property
    def pleaded_guilty(self):
        """ признал ли вину обвиняемый """

        # first check if pleaded not guilty
        for pattern in self.re_plea_not_guilty:

            # if matches, return False: not pleaded guilty
            if pattern.search(self.text):
                return False

        # then check if pleaded guilty
        for pattern in self.re_plea_guilty:

            # if matches, return True: pleaded guilty
            if pattern.search(self.text):
                return True

        # nothing found, return None
        return None

    @property
    def sex(self):

        # matches count
        cnt_male = 0
        cnt_female = 0

        # count male patterns
        for pattern in self.re_male:
            cnt_male += len(re.findall(pattern, self.text))

        # count female patterns
        for pattern in self.re_female:
            cnt_female += len(re.findall(pattern, self.text))

        # is male
        if cnt_male > cnt_female:
            return "male"

        # is female
        if cnt_male < cnt_female:
            return "female"

        # equal
        return None


def txt_get_text(filename):
    """ Получение содержимого текстового файла """

    # open file and read contents
    with io.open(filename, encoding='utf-8') as file:
        text = file.read()

    # return text
    return text


if __name__=="__main__":

    # iterate all files in directory
    for filename in os.listdir("../../Downloads"):

        # if it is text file
        if filename.endswith(".txt"):
           
            # get text file
            text = txt_get_text(filename)

        # no way, continue search
        else: continue

        # parse text
        p = NameParser(text)

        print(filename + " " + str(p.sex))
