# coding: utf-8
from django.http import HttpResponse, HttpResponseNotFound
from django.http import Http404
from django.shortcuts import render
from models import CtgStatus
import config
import os
import json
import utils
import subprocess
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def show_all_category(request):
	all_category = filter(lambda x: not x.startswith('.'), os.listdir(config.CATEGORY_BASEDIR))
	context = {'all_category': all_category}
	return render(request, 'category/all_category.html', context)

def show_category_iteration(request, name):
	category_dir = os.path.join(config.CATEGORY_BASEDIR, name)
	if os.path.isdir(category_dir):
		iterations = map(lambda x: int(x), filter(lambda x: not x.startswith('.'), os.listdir(category_dir)))
		iterations.sort()
		context = { 'category': name, 'iterations': iterations }
		return render(request, 'category/category_iteration.html', context)
	else:
		return HttpResponseNotFound('category %s not exist!' % name)

def can_update(name, iteration):
	# 更新条件：是最新的结果，且ctgstatus为STOP，即没有进行更新一轮的迭代
	category_dir = os.path.join(config.CATEGORY_BASEDIR, name)
	newest = max(map(lambda x: int(x), filter(lambda x: not x.startswith('.'), os.listdir(category_dir))))
	ctgstatus = CtgStatus.objects.filter(category = name)
	return (newest == int(iteration) and ctgstatus and ctgstatus[0].status == config.STATUS_STOP)

def show_iteration_content(request, name, iteration):
	iteration_path = os.path.join(config.CATEGORY_BASEDIR, name, iteration)
	if os.path.isfile(iteration_path):
		instances, patterns = utils.readfile(iteration_path)
		context = { 'instances': instances, 'patterns': patterns, 'can_update': can_update(name, iteration) }
		return render(request, 'category/iteration_content.html', context)
	else:
		return HttpResponseNotFound('iteration %s/%s not exist!' % (name, iteration))

def update_p(request, name, iteration):
	if request.method == 'GET' and request.GET['tp'] and request.GET['i'] and request.GET['delta']:
		tp = request.GET['tp']
		i = int(request.GET['i'])
		delta = float(request.GET['delta'])
		iteration_path = os.path.join(config.CATEGORY_BASEDIR, name, iteration)
		if os.path.isfile(iteration_path) and can_update(name, iteration):
			instances, patterns = utils.readfile(iteration_path)
			utils.ppg(tp, i, delta, instances, patterns)
			utils.write2file(iteration_path, instances, patterns)
			return HttpResponse('')
	return HttpResponseNotFound('iteration %s/%s not exist!' % (name, iteration))

def remove_newest(request, name):
	category_dir = os.path.join(config.CATEGORY_BASEDIR, name)
	newest = max(map(lambda x: int(x), filter(lambda x: not x.startswith('.'), os.listdir(category_dir))))
	if newest > 0:
		os.remove(os.path.join(config.CATEGORY_BASEDIR, name, str(newest)))
		return HttpResponse('')
	return HttpResponseNotFound('not allowed')

def start_cpl(request, name):
	if request.method == 'GET' and request.GET['iternum']:
		ctgstatus = CtgStatus.objects.filter(category = name)
		if ctgstatus and ctgstatus[0].status == config.STATUS_STOP:
			subprocess.Popen(['python', './CategoryCPL.py', name, request.GET['iternum']])
			return HttpResponse('')
	return HttpResponseNotFound('')

def add_new_category_html(request):
	context = { 'exist': [x.category for x in CtgStatus.objects.all()] }
	return render(request, 'category/add_new_category.html', context)

def add_new_category(request):
	if request.method == 'GET' and request.GET['name'] and request.GET['seeds']:
		name = request.GET['name']
		seeds = request.GET['seeds'].split()
		exclusions = request.GET['exclusions'].split()
		####
		# 新建 category 所属的文件夹与 0 轮迭代的文件
		category_dir = os.path.join(config.CATEGORY_BASEDIR, name)
		if not os.path.exists(category_dir):
			os.mkdir(category_dir)
			os.chmod(category_dir, 0o777)
		output = open(os.path.join(category_dir, '0'), 'w')
		output.write('instances\n')
		for i in xrange(len(seeds)):
			output.write('%d\t%s\t-\t-\t1.0\n' % (i, seeds[i]))
		output.close()
		####

		####
		# 在数据库中新建 category 对应的 ctgstatus，并设置相互的互斥关系
		if CtgStatus.objects.filter(category=name):
			print 'The category %s has existed!' % name
			return HttpResponseNotFound('')
		newstatus = CtgStatus(category=name, status=config.STATUS_STOP)
		newstatus.save()
		newstatus.exclusions.add(*list(CtgStatus.objects.filter(category__in=exclusions)))
		for category in exclusions:
			ctgstatus = CtgStatus.objects.get(category=category)
			ctgstatus.exclusions.add(newstatus)
			# ctgstatus.save()
		####

		return HttpResponse('')
	return HttpResponseNotFound('')





