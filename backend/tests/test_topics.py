kw = KeyBERT(model='all-MiniLM-L6-v2') 
test = 'the president discussed healthcare policy and immigration reform during the debate' 
results = kw.extract_keywords(test, keyphrase_ngram_range=(1,3), use_mmr=True, diversity=0.6, top_n=5) 
print('KeyBERT working!') 
[print(f'  {phrase} ({score:.3f})') for phrase, score in results] 
