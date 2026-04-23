import logging

logger = logging.getLogger(__name__)

kw = KeyBERT(model='all-MiniLM-L6-v2') # type: ignore
test = 'the president discussed healthcare policy and immigration reform during the debate'
results = kw.extract_keywords(test, keyphrase_ngram_range=(1,3), use_mmr=True, diversity=0.6, top_n=5)

logger.info('KeyBERT working!')
for phrase, score in results:
	logger.info('  %s (%.3f)', phrase, score)
