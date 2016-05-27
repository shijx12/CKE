# coding: utf-8
from django.http import HttpResponse, HttpResponseNotFound
from django.http import Http404
from django.shortcuts import render
from models import RltStatus
import config
import os
import json
import utils
import subprocess
import sys
reload(sys)
sys.setdefaultencoding('utf-8')



def show_all_relation(request):
	all_relation = filter(lambda x: not x.startswith('.'), os.listdir(config.RELATION_BASEDIR))
	context = {'all_relation': all_relation}
	return render(request, 'relation/all_relation.html', context)

def show_relation_iteration(request, name):
	relation_dir = os.path.join(config.RELATION_BASEDIR, name)
	if os.path.isdir(relation_dir):
		iterations = map(lambda x: int(x), filter(lambda x: not x.startswith('.'), os.listdir(relation_dir)))
		iterations.sort()
		context = { 'relation': name, 'iterations': iterations }
		return render(request, 'relation/relation_iteration.html', context)
	else:
		return HttpResponseNotFound('relation %s not exist!' % name)

def can_update(name, iteration):
	# 更新条件：是最新的结果，且rltstatus为STOP，即没有进行更新一轮的迭代
	relation_dir = os.path.join(config.RELATION_BASEDIR, name)
	newest = max(map(lambda x: int(x), filter(lambda x: not x.startswith('.'), os.listdir(relation_dir))))
	rltstatus = RltStatus.objects.filter(relation = name)
	return (newest == int(iteration) and rltstatus and rltstatus[0].status == config.STATUS_STOP)

def show_iteration_content(request, name, iteration):
	iteration_path = os.path.join(config.RELATION_BASEDIR, name, iteration)
	if os.path.isfile(iteration_path):
		# instances, patterns = utils.readfile(iteration_path)
		instances, patterns = utils.old_readfile(iteration_path)
		context = { 'instances': instances, 'patterns': patterns, 'can_update': can_update(name, iteration) }
		return render(request, 'relation/iteration_content.html', context)
	else:
		return HttpResponseNotFound('iteration %s/%s not exist!' % (name, iteration))

# def update_p(request, name, iteration):
# 	if request.method == 'GET' and request.GET['tp'] and request.GET['i'] and request.GET['delta']:
# 		tp = request.GET['tp']
# 		i = int(request.GET['i'])
# 		delta = float(request.GET['delta'])
# 		iteration_path = os.path.join(config.RELATION_BASEDIR, name, iteration)
# 		if os.path.isfile(iteration_path) and can_update(name, iteration):
# 			instances, patterns = utils.readfile(iteration_path)
# 			utils.ppg(tp, i, delta, instances, patterns)
# 			utils.write2file(iteration_path, instances, patterns)
# 			return HttpResponse('')
	return HttpResponseNotFound('iteration %s/%s not exist!' % (name, iteration))

def remove_newest(request, name):
	relation_dir = os.path.join(config.RELATION_BASEDIR, name)
	newest = max(map(lambda x: int(x), filter(lambda x: not x.startswith('.'), os.listdir(relation_dir))))
	if newest > 0:
		os.remove(os.path.join(config.RELATION_BASEDIR, name, str(newest)))
		return HttpResponse('')
	return HttpResponseNotFound('not allowed')

def start_cpl(request, name):
	if request.method == 'GET' and request.GET['iternum']:
		rltstatus = RltStatus.objects.filter(relation = name)
		if rltstatus and rltstatus[0].status == config.STATUS_STOP:
			subprocess.Popen(['python', './RelationCPL.py', name, request.GET['iternum']])
			return HttpResponse('')
	return HttpResponseNotFound('')

def add_new_relation_html(request):
	context = { 'exist': [x.relation for x in RltStatus.objects.all()] }
	return render(request, 'relation/add_new_relation.html', context)

def add_new_relation(request):
	if request.method == 'GET' and request.GET['name'] and request.GET['seeds']:
		name = request.GET['name']
		seeds = request.GET['seeds'].split()
		exclusions = request.GET['exclusions'].split()
		####
		# 新建 relation 所属的文件夹与 0 轮迭代的文件
		relation_dir = os.path.join(config.RELATION_BASEDIR, name)
		if not os.path.exists(relation_dir):
			os.mkdir(relation_dir)
			os.chmod(relation_dir, 0o777)
		output = open(os.path.join(relation_dir, '0'), 'w')
		output.write('instances\n')
		for i in xrange(len(seeds)):
			output.write('%d\t%s\t-\t-\t1.0\n' % (i, seeds[i]))
		output.close()
		####

		####
		# 在数据库中新建 relation 对应的 rltstatus，并设置相互的互斥关系
		if RltStatus.objects.filter(relation=name):
			print 'The relation %s has existed!' % name
			return HttpResponseNotFound('')
		newstatus = RltStatus(relation=name, status=config.STATUS_STOP)
		newstatus.save()
		newstatus.exclusions.add(*list(RltStatus.objects.filter(relation__in=exclusions)))
		for relation in exclusions:
			rltstatus = RltStatus.objects.get(relation=relation)
			rltstatus.exclusions.add(newstatus)
			# rltstatus.save()
		####

		return HttpResponse('')
	return HttpResponseNotFound('')





