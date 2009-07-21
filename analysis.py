#!/usr/bin/env python

#system
import igraph as ig
from time import ctime
from optparse import OptionParser
import os, sys, re
import gc
import numpy

#project
from tablr import Tablr

## GLOBAL VARIABLES

## FUNCTIONS



def averageDistance(g, weighted=True):
    isinstance(g, ig.Graph) # helper for wing
    dSum = 0.
    step = 1000
    n = len(g.vs)
    for i in range(0, n, step):
        ##if not (i+1) % 100:
        ##    print 'Step:', i
        ##    print 1.*dSum*step/i
        uplimit = min(n, i+step)

        # distances from nodes in range (i, i+step) to all the other nodes
        if weighted:
            aDistances = g.shortest_paths(range(i, uplimit), weights='length')
        else:
            aDistances = g.shortest_paths(range(i, uplimit))

        dSum += 1.*sum([sum(d) for d in aDistances]) / (n-1) / (uplimit - i)

    avg_dist = 1.*dSum / len(range(0, n, step))
    return avg_dist


def efficiency(g):
    isinstance(g, ig.Graph) # helper for wing
    effSum = 0.
    step = 1000
    n = len(g.vs)
    for i in range(0, n, step):
        ##if not (i+1) % 100:
        ##    print 'Step:', i
        ##    print 1.*dSum*step/i
        uplimit = min(n, i+step)

        # distances from nodes in range (i, i+step) to all the other nodes
        aDistances = g.shortest_paths(range(i, uplimit), weights='length')
        effSum += 1.*sum(sum(1./numpy.array([e for e in d if e])) for d in aDistances)

    efficiency = effSum/(1.*n*(n-1)) # maybe there should be a factor of 2 somewhere (directed graph)
    return efficiency


def set_weighted_degree(g, type=ig.IN):
    #todo: improve self-loops check
    stype = type == ig.IN and "in" or "out"
    k = 'weighted_%sdegree' % stype

    for node in g.vs:
        edges = g.adjacent(node.index, type=type)
        g_edges = (e for e in edges if not g.is_loop(e))
        node[k] = sum(g.es[eid]['weight'] for eid in g_edges)


if __name__ == '__main__':
    op = OptionParser('%prog [options] graph')

    op.add_option('--as-table', action="store_true", dest="as_table",
        help="Format output as a table row")
    op.add_option('-d', '--details', action="store_true", dest="details",
        help="Print details about this graph (# of vertexes and # of edges)")
    op.add_option('-e', '--degree', action="store_true", dest="degree",
        help="Print the mean vertex-vertex distance of the graph")
    op.add_option('-r', '--density', action="store_true", dest="density",
        help="Print the density of the graph")
    op.add_option('-t', '--transitivity', action="store_true", dest="transitivity")
    op.add_option('-i', '--distance', action="store_true", dest="distance")
    op.add_option('-f', '--efficiency', action="store_true", dest="efficiency")
    op.add_option('-s', '--summary', action="store_true", dest="summary")
    op.add_option('-c', '--centrality', action="store_true", dest="centrality")
    op.add_option('-p', '--plot', action="store_true", dest="plot")
    op.add_option('--histogram', action="store_true", dest="histogram")
    op.add_option('-g', '--gnuplot', action="store_true", dest="gnuplot")
    op.add_option('--power-law', action="store_true", dest="power_law")

    (options, args) = op.parse_args()

    if len(args) != 1:
        print "Insert one (and only one) file to process\n"
        op.print_help()
        sys.exit(2)

    fn = args[0]
    s = os.path.split(fn)[1]
    lang = s[:s.index('wiki')]
    res = re.search('wiki-(\d{4})(\d{2})(\d{2})',s)
    date = ''.join([res.group(x) for x in xrange(1,4)])
    g = ig.load(fn)
    isinstance(g, ig.Graph) # helper for wing
    g.es['length'] = 1./numpy.array(g.es['weight'])

    if options.as_table:
        tablr = Tablr()
        tablr.start(1024*16, lang)

    if options.details:
        print " * vertexes: %d" % (len(g.vs),)
        print " * edges: %d" % (len(g.es),)

        nodes_with_outdegree = len(g.vs.select(_outdegree_ge=1))
        nodes_with_indegree = len(g.vs.select(_indegree_ge=1))

        print " * #nodes with out edges: %d (%6f%%)" % (nodes_with_outdegree, 100.*nodes_with_outdegree/len(g.vs))
        print " * #nodes with in edges: %d (%6f%%)" % (nodes_with_indegree, 100.*nodes_with_indegree/len(g.vs))
        print " * 5 max numMsg on edges : %s" % (', '.join(str(idx) for idx in sorted(g.es['weight'], reverse=True)[:5]),)
        print " * reciprocity : %6f" % g.reciprocity()
        print " * diameter : %6f" % g.diameter(weights='length')

        print " * Average weights : %6f" % numpy.average(g.es['weight'])


    if options.density:
        print " * density: %.10f" % (g.density(),)

        #print " * calculated density: %.10f" % (1.*len(g.es)/lenvs/(lenvs-1))

    if options.degree:
        ind = numpy.array(g.degree(type=ig.IN))
        outd = numpy.array(g.degree(type=ig.OUT))
        mid = numpy.average(ind)
        mod = numpy.average(outd)

        print " * mean IN/OUT degree (no weights): %f" % mid
        print " * 5 max IN degree (no weights): %s" % ', '.join(map(str, sorted(ind, reverse=True)[:5]))
        print " * 5 max OUT degree (no weights): %s" % ', '.join(map(str, sorted(outd, reverse=True)[:5]))

        print " * variance IN Degree (no weights): %f" % numpy.var(ind)
        print " * variance OUT Degree (no weights): %f" % numpy.var(outd)

    if options.transitivity:
        #print " * transitivity: %f" % (nx.transitivity(g), )
        pass

    if options.summary:
        print " * summary: %s" % (g.summary(), )

    if options.distance:
        vc = g.clusters()
        max_clusters = sorted(vc.sizes(), reverse=True)[:5]
        giant = vc.giant()

        print " * length 5 max clusters: %s" % ', '. join(map(str, max_clusters))
        print " * #node in 5 max clusters/#all nodes: %s" % ', '.join("%6f" % (1.*cluster_len/len(g.vs),) for cluster_len in max_clusters)

    if options.distance:
        print " * average distance in the giant component: %f" % averageDistance(giant)
        print " * average hops in the giant component: %f" % averageDistance(giant, False)

        #print "Average distance 2: %f" % giant.average_path_length(True, False)


    if options.efficiency:
        print " * efficiency: %f" % efficiency(g)


    if options.plot or options.histogram or options.power_law or options.centrality:
        set_weighted_degree(g)

    if options.centrality:
        g.vs['bw'] = g.betweenness(weights='length', directed = True)
        #g.vs['ev'] = g.evcent(weights='weight') # eigenvector centrality
        g.vs['pr'] = g.pagerank(weights='weight') # pagerank
        set_weighted_degree(g, type=ig.OUT)
        total_weights = sum(g.es['weight'])
        max_edges = len(g.vs)*(len(g.vs)-1)

        print " * Average betweenness : %6f" % (numpy.average(g.vs['bw'])/max_edges,)
        #print " * Average eigenvector centrality : %6f" % numpy.average(g.vs['ev'])
        print " * Average pagerank : %6f" % numpy.average(g.vs['pr'])
        print " * Average IN degree centrality (weighted): %6f" % numpy.average(g.vs['weighted_indegree'])
        print " * Average OUT degree centrality (weighted) : %6f" % numpy.average(g.vs['weighted_outdegree'])

    if options.power_law:
        indegrees = g.vs['weighted_indegree']

        alpha_exp = ig.statistics.power_law_fit(indegrees, xmin=1)

        print " * alpha exp of the power law : %6f " % alpha_exp

    if options.histogram:
        # group
        nogrp_indegrees = g.vs.select(sysop_ne=True, bureaucrat_ne=True, steward_ne=True, founder_ne=True, bot_ne=True)['indegree']
        nogrp_list = [(degree, 1) for degree in nogrp_indegrees if degree]

        sysops_indegrees = g.vs.select(sysop=True, bureaucrat_ne=True, steward_ne=True, founder_ne=True, bot_ne=True)['indegree']
        sysops_list = [(degree, 2) for degree in sysops_indegrees if degree]

        burs_indegrees = g.vs.select(bureaucrat=True, steward_ne=True, founder_ne=True, bot_ne=True)['indegree']
        burs_list = [(degree, 3) for degree in burs_indegrees if degree]

        stewards_indegrees = g.vs.select(steward=True, founder_ne=True, bot_ne=True)['indegree']
        stewards_list = [(degree, 4) for degree in stewards_indegrees if degree]

        founders_indegrees = g.vs.select(founder=True, bot_ne=True)['indegree']
        founders_list = [(degree, 5) for degree in founders_indegrees if degree]

        bots_indegrees = g.vs.select(bot=True)['indegree']
        bots_list = [(degree, 6) for degree in bots_indegrees if degree]

        if options.gnuplot:
            f = open('hist.dat', 'w')
        else:
            f = open('%swiki-%s-hist.dat' % (lang, date), 'w')

        all_list = sorted(sysops_list + nogrp_list + burs_list + stewards_list + founders_list + bots_list, reverse=True)

        for indegree, grp in sorted(sysops_list + nogrp_list + burs_list + stewards_list + founders_list + bots_list, reverse=True):
            for i in range(grp - 1):
                print >>f, 0,
            print >>f, indegree,
            for i in range(grp, 6):
                print >>f, 0,
            print >>f, ""
        f.close()

    if options.gnuplot:
        from popen2 import Popen3

        process = Popen3('gnuplot hist.gnuplot')
        process.wait()

        os.rename('hist.png', '%swiki-%s-hist.png' % (lang, date))
        os.rename('hist.dat', '%swiki-%s-hist.dat' % (lang, date))


    if options.plot:
        import math
        bots = g.vs.select(bot=True)
        bots['color'] = ('purple',)*len(bots)

        burs = g.vs.select(bureaucrat=True)
        burs['color'] = ('blue',)*len(burs)

        sysops = g.vs.select(sysop=True)
        sysops['color'] = ('yellow',)*len(sysops)

        bur_sysops = g.vs.select(bureaucrat=True, sysop=True)
        bur_sysops['color'] = ('orange',)*len(bur_sysops)

        g.vs['size'] = [math.sqrt(v['indegree']+1)*10 for v in g.vs]

        ig.plot(g, target=lang+"_general.png", bbox=(0,0,4000,2400), edge_color='grey', layout='fr')
        weights = g.es['weight']
        max_weight = max(weights)

        g.es['color'] = [(255.*e['weight']/max_weight, 0., 0.) for e in g.es]
        g.es['width'] = weights

        ig.plot(g, target=lang+"_weighted_edges.png", bbox=(0,0,4000,2400), layout='fr', vertex_label=' ')


    if options.as_table:
        tablr.stop()

        tablr.printHeader()
        tablr.printData()
