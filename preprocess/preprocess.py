# coding:utf-8

import re
import langconv
import sys
import jieba
import jieba.posseg as pseg
reload(sys)
sys.setdefaultencoding('utf-8')

USER_DIC = './output/wikidict.txt'
converter = langconv.Converter('zh-hans')

def getPlainText():
	input_file = './output/step1.xml'
	output = open('./output/step2.txt', 'w')

	rmstrs = [
		'<div[\s\S]*?</div>',
		'<doc[^>]*?>',
		'</doc>',
		'\([^\)]*?\)',
		'（[\s\S]*?(）|$)',
		'^[\s\S]*?）',
	]
	rmstr = '|'.join(map(lambda x: '(' + x + ')', rmstrs)).decode('utf-8')
	rmpt = re.compile(rmstr)
	for line in open(input_file):
		line = rmpt.sub('', line.strip().decode('utf-8'))
		if len(line) < 10 or line.lower().startswith('category:') or line.lower().startswith('file:') or line.lower().startswith('wikipedia:') or line.lower().startswith('portal:'):
			continue
		line = converter.convert(line).encode('utf-8')
		# print line
		# pause = raw_input()
		output.write(line + '\n')
	output.close()

def getEntries():
	input_file = './output/step1.xml'
	output = open(USER_DIC, 'w')
	rmstrs = [
		'\([^\)]*?\)',
		'（[\s\S]*?(）|$)',
		'^[\s\S]*?）',
		'Category:',
	]
	rmstr = '|'.join(map(lambda x: '(' + x + ')', rmstrs)).decode('utf-8')
	rmpt = re.compile(rmstr)	#remove_pattern
	etpt = re.compile('title="([\s\S]*?)[">]') #entry_pattern
	for line in open(input_file):
		entry = etpt.search(line.strip().decode('utf-8'))
		if entry:
			entry = rmpt.sub('', entry.group(1))
			if entry.lower().startswith('file:') or entry.lower().startswith('wikipedia:') or entry.lower().startswith('portal:'):
				continue
			entry = converter.convert(entry).encode('utf-8')
			# print entry
			# pause = raw_input()
			output.write(entry + ' n\n')
	output.close()

def posseg():
	input_file = './output/step2.txt'
	jieba.load_userdict(USER_DIC)
	output = open('./output/step3.txt', 'w')
	for line in open(input_file):
		words = pseg.cut(line.strip())
		for w in words:
			output.write(w.word + '/' + w.flag + ' ')
		output.write('\n')
		# 	print w.word + '/' + w.flag,
		# print
		# pause = raw_input()
	output.close()

if __name__ == '__main__':
	getEntries()
	getPlainText()
	posseg()




