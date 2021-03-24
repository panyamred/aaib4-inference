from models import CustomResponse, Status
from anuvaad_auditor.loghandler import log_info, log_exception
from utilities import MODULE_CONTEXT
import os
import json
import sys
import re
import utilities.sentencepiece_util as sp
import utilities.fairseq_sentence_processor as sentence_processor
import config
import datetime
from services import load_models


class FairseqTranslateService:
    @staticmethod
    def simple_translation(inputs):
        out = {}
        i_src, tgt = list(), list()
        tagged_tgt = list()
        tagged_src = list()
        sentence_id = list()
        tp_tokenizer = None

        try:
            for i in inputs:
                sentence_id.append(i.get("s_id") or "NA")
                if any(v not in i for v in ["src", "id"]):
                    log_info("either id or src missing in some input", MODULE_CONTEXT)
                    out = CustomResponse(Status.ID_OR_SRC_MISSING.value, inputs)
                    return out

                log_info("input sentence:{}".format(i["src"]), MODULE_CONTEXT)
                i_src.append(i["src"])
                tag_src = i["src"]

                if i["id"] == 100:
                    "hindi-english"
                    translation = encode_translate_decode(i, "hi", "en")
                elif i["id"] == 101:
                    "bengali-english"
                    translation = encode_translate_decode(i, "bn", "en")
                elif i["id"] == 102:
                    "tamil-english"
                    translation = encode_translate_decode(i, "ta", "en")

                else:
                    log_info(
                        "unsupported model id: {} for given input".format(i["id"]),
                        MODULE_CONTEXT,
                    )
                    raise Exception(
                        "Unsupported Model ID - id: {} for given input".format(i["id"])
                    )

                tag_tgt = translation[0]
                log_info(
                    "simple translation-experiment-{} output: {}".format(
                        i["id"], translation
                    ),
                    MODULE_CONTEXT,
                )
                tgt.append(translation[0])
                tagged_tgt.append(tag_tgt)
                tagged_src.append(tag_src)

            out["response_body"] = [
                {
                    "tgt": tgt[i],
                    "tagged_tgt": tagged_tgt[i],
                    "tagged_src": tagged_src[i],
                    "s_id": sentence_id[i],
                    "src": i_src[i],
                }
                for i in range(len(tgt))
            ]
            out = CustomResponse(Status.SUCCESS.value, out["response_body"])
        except Exception as e:
            status = Status.SYSTEM_ERR.value
            status["why"] = str(e)
            log_exception(
                "Unexpected error:%s and %s" % (e, sys.exc_info()[0]), MODULE_CONTEXT, e
            )
            out = CustomResponse(status, inputs)

        return out

class FairseqAutoCompleteTranslateService:
    @staticmethod
    def constrained_translation(inputs):
        inputs = inputs
        out = {}
        sentence_id = list()
        i_src, tgt = list(), list()
        tagged_tgt, tagged_src = list(), list()

        try:
            for i in inputs:
                sentence_id.append(i.get("s_id") or "NA")
                if any(v not in i for v in ["src", "id"]):
                    log_info("either id or src missing in some input", MODULE_CONTEXT)
                    out = CustomResponse(Status.ID_OR_SRC_MISSING.value, inputs)
                    return out

                log_info("input sentences:{}".format(i["src"]), MODULE_CONTEXT)
                i_src.append(i["src"])
                tag_src = i["src"]

                if i["id"] == 103:
                    "hindi-english"
                    translation = encode_itranslate_decode(i, "hi", "en")
                elif i["id"] == 104:
                    "bengali-english"
                    translation = encode_itranslate_decode(i, "bn", "en")
                elif i["id"] == 105:
                    "tamil-english"
                    translation = encode_itranslate_decode(i, "ta", "en")
                else:
                    log_info(
                        "Unsupported model id: {} for given input".format(i["id"]),
                        MODULE_CONTEXT,
                    )
                    raise Exception(
                        "Unsupported Model ID - id: {} for given input".format(i["id"])
                    )

                tag_tgt = translation
                log_info(
                    "translate_function-experiment-{} output: {}".format(
                        i["id"], translation
                    ),
                    MODULE_CONTEXT,
                )
                tgt.append(translation)
                tagged_tgt.append(tag_tgt), tagged_src.append(tag_src)

            out["response_body"] = [
                {
                    "tgt": tgt[i],
                    "s_id": sentence_id[i],
                    "src": i_src[i],
                    "tagged_tgt": tagged_tgt[i],
                    "tagged_src": tagged_src[i],
                }
                for i in range(len(tgt))
            ]
            out = CustomResponse(Status.SUCCESS.value, out["response_body"])
        except ServerModelError as e:
            status = Status.SEVER_MODEL_ERR.value
            status["message"] = str(e)
            log_exception(
                "ServerModelError error in TRANSLATE_UTIL-translate_func: {} and {}".format(
                    e, sys.exc_info()[0]
                ),
                MODULE_CONTEXT,
                e,
            )
            out = CustomResponse(status, inputs)
        except Exception as e:
            status = Status.SYSTEM_ERR.value
            status["message"] = str(e)
            log_exception(
                "Unexpected error:%s and %s" % (e, sys.exc_info()[0]), MODULE_CONTEXT, e
            )
            out = CustomResponse(status, inputs)

        return out


def encode_itranslate_decode(i, src_lang, tgt_lang):
    try:
        i["src"] = [i["src"]]
        i["target_prefix"] = [i["target_prefix"]]

        translator = load_models.loaded_models[i["id"]]
        source_bpe = load_models.bpes[i["id"]][0]
        target_bpe = load_models.bpes[i["id"]][1]
        i["src"] = sentence_processor.preprocess(i["src"], src_lang)
        i["src"] = apply_bpe(i["src"], source_bpe)
        # apply bpe to constraints with target bpe
        prefix = apply_bpe(i["target_prefix"], target_bpe)
        # log_info("BPE encoded sent: %s" % i["src"], MODULE_CONTEXT)
        i_final = sentence_processor.apply_lang_tags(i["src"], src_lang, tgt_lang)
        translation = translator.translate(i_final, constraints=prefix)
        translation = sentence_processor.postprocess(translation, tgt_lang)
        return translation

    except Exception as e:
        log_exception(
            "Unexpexcted error in encode_itranslate_decode: {} and {}".format(
                e, sys.exc_info()[0]
            ),
            MODULE_CONTEXT,
            e,
        )
        raise


def encode_translate_decode(i, src_lang, tgt_lang):
    try:
        i["src"] = [i["src"]]
        print(i["src"])
        log_info("Inside encode_translate_decode function", MODULE_CONTEXT)
        translator = load_models.loaded_models[i["id"]]
        source_bpe = load_models.bpes[i["id"]][0]
        # target_bpe = load_models.bpes[i["id"]][1]
        i["src"] = sentence_processor.preprocess(i["src"], src_lang)
        i["src"] = apply_bpe(i["src"], source_bpe)
        log_info("BPE encoded sent: %s" % i["src"], MODULE_CONTEXT)
        i_final = sentence_processor.apply_lang_tags(i["src"], src_lang, tgt_lang)
        translation = translator.translate(i_final)
        translation = sentence_processor.postprocess(translation, tgt_lang)
        return translation
    except ServerModelError as e:
        log_exception(
            "ServerModelError error in encode_translate_decode: {} and {}".format(
                e, sys.exc_info()[0]
            ),
            MODULE_CONTEXT,
            e,
        )
        raise

    except Exception as e:
        log_exception(
            "Unexpexcted error in encode_translate_decode: {} and {}".format(
                e, sys.exc_info()[0]
            ),
            MODULE_CONTEXT,
            e,
        )
        raise


def apply_bpe(sents, bpe):
    return [bpe.process_line(sent) for sent in sents]