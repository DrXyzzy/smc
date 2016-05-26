#!/usr/bin/env python3

"""
HAPROXY management/deployment script

"""

import os, shutil, sys, tempfile
join = os.path.join

# Boilerplate to ensure we are in the directory fo this path and make the util module available.
SCRIPT_PATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_PATH, '..', 'util')))
import util

NAME='haproxy'

def build(tag, rebuild):
    # Next build smc-hub, which depends on smc-hub-base.
    v = ['sudo', 'docker', 'build', '-t', tag]
    if rebuild:  # will cause a git pull to happen
        v.append("--no-cache")
    v.append('.')
    util.run(v, path=join(SCRIPT_PATH, 'image'))

def build_docker(args):
    tag = util.get_tag(args, NAME)
    build(tag, args.rebuild)
    if not args.local:
        util.gcloud_docker_push(tag)

def images_on_gcloud(args):
    for x in util.gcloud_images(NAME):
        print("%-20s%-60s"%(x['TAG'], x['REPOSITORY']))

def run_on_kubernetes(args):
    args.local = False # so tag is for gcloud
    tag = util.get_tag(args, NAME)
    print("tag='{tag}', replicas='{replicas}'".format(tag=tag, replicas=args.replicas))
    t = open(join('conf', '{name}.template.yaml'.format(name=NAME))).read()
    with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w') as tmp:
        tmp.write(t.format(image=tag, replicas=args.replicas))
        tmp.flush()
        util.update_deployment(tmp.name)

def stop_on_kubernetes(args):
    util.stop_deployment(NAME)

def ssl(args):
    path = os.path.abspath(join(SCRIPT_PATH, '..', '..', 'data', 'secrets'))
    if not os.path.exists(path):
        os.makedirs(path)
    util.create_secret('ssl-cert', join(path, 'sagemath.com', 'nopassphrase.pem'))

def expose(args):
    util.run(['kubectl', 'expose', 'deployment', NAME, '--type=LoadBalancer'])

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Control deployment of {name}'.format(name=NAME))
    subparsers = parser.add_subparsers(help='sub-command help')

    sub = subparsers.add_parser('build', help='build docker image')
    sub.add_argument("-t", "--tag", default="", help="tag for this build")
    sub.add_argument("-r", "--rebuild", action="store_true", help="rebuild from scratch")
    sub.add_argument("-l", "--local", action="store_true",
                     help="only build the image locally; don't push it to gcloud docker repo")
    sub.set_defaults(func=build_docker)

    sub = subparsers.add_parser('run', help='create/update {name} deployment on the currently selected kubernetes cluster'.format(name=NAME))
    sub.add_argument("-t", "--tag", default="", help="tag of the image to run (default: most recent tag)")
    sub.add_argument("-r", "--replicas", default=3, help="number of replicas") # todo -- need to run as daemon-- one on each node for best HA
    sub.set_defaults(func=run_on_kubernetes)

    sub = subparsers.add_parser('stop', help='delete the deployment')
    sub.set_defaults(func=stop_on_kubernetes)

    sub = subparsers.add_parser('images', help='list {name} tags in gcloud docker repo, from newest to oldest'.format(name=NAME))
    sub.set_defaults(func=images_on_gcloud)

    sub = subparsers.add_parser('ssl', help='load data/secrets/sagemath.com/nopassphrase.pem needed for ssl by the {name} pods'.format(name=NAME))
    sub.set_defaults(func=ssl)

    sub = subparsers.add_parser('expose', help='make deployment publicly visible via a public load balancer')
    sub.set_defaults(func=expose)

    util.add_autoscale_parser(NAME, subparsers)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
