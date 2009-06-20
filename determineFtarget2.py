#! /usr/bin/env python
# coding: utf-8

import os
import numpy
import sys
from pdb import set_trace
import getopt

last_target_value_replacement = None  # 1e-5  # None for nothing
append_final_target_value = True      # 1e-8 is appended

# add path to bbob_pproc  
#filepath = '/home/fst/coco/BBOB/code/python/bbob_pproc/'
#sys.path.append(os.path.join(filepath, os.path.pardir))
if __name__ == "__main__":
    # append path without trailing '/bbob_pproc', using os.sep fails in mingw32
    #sys.path.append(filepath.replace('\\', '/').rsplit('/', 1)[0])
    (filepath, filename) = os.path.split(sys.argv[0])
    # Test system independent method:
    sys.path.append(os.path.join(filepath, os.path.pardir))

from bbob_pproc import pproc2

### Class Definitions ###

class FunTarget:
    """ Determines the largest (easiest) of the recorded function values where 
        the best algorithm needs more than (E)RT=i*D function evaluations for
        i = 1,10,100... 
        The minimal target function value 1e-8 might be appended to the list, 
        or the last element is set to be not larger than 1e-5. 

        Class Attributes:
        minFtarget - target function values that could never be achieved
                     within D, 10D, 100D,... evaluations for 
                     given dimension, function (array)
        medianFtarget - target function values that could never be 
                     achieved within an ERT of D,10D, 100D,... for 
                     given dimension, function (array)
        ert - (E)RT/DIM corresponding to minFtarget (array)
    """
   
    def __init__(self, dataset, dim):
        """ TODO: what type are the input arguments?
        """

        self.minFtarget = [] 
        self.medianFtarget = [] 
        self.ert = [] 

        maxErtAll = 0
        for alg in dataset:
            maxErtAll = max(maxErtAll, alg.ert[-1])

        for i in range(0, 1 + int(numpy.log10(maxErtAll))):

            # collect smallest function value reached within ERT <= D * 10**i for all algorithms
            targetValues = []
            for alg in dataset:
                targetValues.append(alg.target[sum(alg.ert <= dim * 10**i) - 1])

            # collect smallest function value reached in any single run within D * 10**i fevals
            alltargetValues = []
            for alg in dataset:
                for row in reversed(alg.evals):
                  if min(row[1:][numpy.isfinite(row[1:])]) <= dim * 10**i:
                      alltargetValues.append(row[0])
                      break
                
            # determine min and median for all algorithms
            self.minFtarget.append(numpy.min(alltargetValues) / 10**(0.1))
            self.medianFtarget.append(numpy.min(targetValues) / 10**(0.1))  # min was median
            self.ert.append(10**i)
            
	# set trailing of equal values to NaN: 
        # TODO: this does not work for the profile plots
        # TODO: this should become part of the target value pre-processing for the run length distributions
	for i in range(1,len(self.minFtarget)):
	    if self.minFtarget[i-1] == self.minFtarget[i]:
                pass
                # self.minFtarget[i-1] = numpy.NaN

	# modify end of lists
        self.minFtarget = numpy.array(self.minFtarget)
        if last_target_value_replacement is not None:  # replace last value with e.g. min(val, 1e-5)
            finalval = last_target_value_replacement
            idx = numpy.where(self.minFtarget >= 1e-8)[0][-1]
            if self.minFtarget[idx] > finalval:
                self.minFtarget[idx] = finalval
        if append_final_target_value:  # add e.g. 1e-8 as last value
            finalval = 1e-8
            idx = numpy.where(self.minFtarget > finalval)[0][-1]
            if len(self.minFtarget) > idx+1:  # only if space is left
                self.minFtarget[idx+1] = finalval
            
            
        # check lists
        if 1 < 3:  # should not be necessary, including some testing
	    self.minFtarget[self.minFtarget < 1e-8] = numpy.NaN
	    if len(self.minFtarget) == 0:
		print 'empty minFtarget list in determineFtarget2.py'
	    self.medianFtarget = numpy.array(self.medianFtarget)
	    self.medianFtarget[self.medianFtarget < 1e-8] = numpy.NaN
	    if len(self.medianFtarget) == 0:
		print 'empty medianFtarget list in determineFtarget2.py'
	    print 'f', dataset[0].funcId, dim, '-D', ':'
	    print self.minFtarget
	    print self.medianFtarget
	    if dataset[0].funcId == 24 and dim == 20:
		pass
		# set_trace()
      
### Function definitons ###

def usage():
    print main.__doc__

def writeTable(data,dim,suffix=None, whichvalue = 'min'):
    """ Write data in tex-files for creating tables.

        Inputvalues:
        data - values which are to be processed (list)
        dim - corresponding dimension. There will be
              at least one table per dimension.
        suffix - If not all data can fit within one side
                 2 files (*_part1.tex and *_part2.tex) will
                 be created. 
        whichvalue - determines wheter the min ('min') values
                     or the median ('median') values are displayed. 
    """

    # parameter
    fontSize = 'tiny'   
    
    # define header and format of columns
    header = ['$evals/D$'] 
    format = ['%1e']
    for id in range(0,len(data)):
        header.append('$f_{' + str(data[id]['funcId']) + '}$')
        format.append('%1.1e')

    # create latex string for table definiton
    tabColumns = '@{$\;$}r@{$\;$}'
    tabColumns += ('|' + (len(header) - 1) * '@{$\;$}c@{$\;$}')

    # open file
    if suffix is None:
        filename = whichvalue + 'ftarget_dim' + str(dim) 
    else:
        filename = whichvalue + 'ftarget_dim' + str(dim) + '_part' + str(suffix)
    try:
        f = open(filename + '.tex','w')
    except ValueError:
        print 'Error opening '+ filename +'.tex'

    # Write tabular environment
    f.write('\\begin{' + fontSize + '} \n')
    f.write('\\begin{tabular}{' + tabColumns + '} \n')

    # write header
    f.write(' & '.join(header) + '\\\\ \n \hline \n')

    # write data
    i = 0
    maxLength = 0
    # write each row separately
    while True:
        tableData = [10**i]
        # create data for each function
        for fun in range(0,len(data)):
            try:
                tableData.append(data[fun][whichvalue][i]) 
            except:
                # if no entry exist write nan
                tableData.append(numpy.nan)
    
            # create termination condition
            if i == 0 and len(data[fun]['ert']) > maxLength:
                maxLength = len(data[fun]['ert'])

        #print tableData

        # write row in latex format
        writeArray(f,tableData,format,'scriptstyle')

        # check termination condition
        if maxLength > i+1:
            i += 1
        else:
            break

    # finish writing and write caption
    f.write('\end{tabular} \n')
    if suffix is None or suffix == 2:
        f.write('\caption{target function value ('+ whichvalue +
                ') for increasing problem difficulty in '+ str(dim) +'-D} \n')  
    f.write('\end{' + fontSize + '} \n')

    # close file
    f.close()
    if not f.closed:
        raise ValueError, ('File ' + filename +'.tex is not closed!')

def writeArray(file, vector, format, fontSize, sep=' & ', linesep='\\\\ \n',
               suppress_entry=None):
    """ Writes components of an numeric array in LaTex file with additional
        Tex-formating features. Negative numbers are printed positive but in
        italics.

        Inputs:
        file - file in which the output is written to
        vector - 1d-array with only numeric entries
        format - format specifier for each column.
            CAVE: numbers are only printed correctly,
                  if format specifies two numbers of prec.
        fontSize - size of characters in math environment

        Optional Inputs:
        sep - string which is written between the numeric elements
        format - format for the numeric values (e.g. 'e','f')
        suppress_entry - list of boolean of len of vector, if true
           a '.' is written. Useful to not repeat the same line of
           function values again.
    """

    # TODO (see CAVE above): I think the written numbers are only correct, if
    # the input format specifies two numbers of precision. Otherwise the
    # rounding procedure is wrong.

    # handle input arg
    if suppress_entry is None:
        suppress_entry = len(vector) * (False,)

    # Loop through vector
    for i, x in enumerate(vector):

        # Filter entries to suppress, nan, inf...
        if suppress_entry[i]:
            tmp2 = '.'
        elif numpy.isinf(x):
            tmp2 = '\infty'
        elif numpy.isnan(x):
            tmp2 = '-'

        elif format[i].endswith('e'):

            # set minimum to 1e-8
            if x>0 and x<1e-8:
                x = 0.00000001

            # Split number and sign+exponent
            try:
                tmp = str(format[i]%x).split('e')
            except TypeError:
                print format[i]
                print x
                print type(x)
                print type(format[i])

            # Generate Latex entry
            # It is assumed that all entries range between 10e-9 and 10e9
            if i == 0:  # ert/dim values
                if x <= 100 :
                    tmp2 = str(int(round(x)))  # tmp[0][0]
                else:
                    tmp2 = (tmp[0][0] + '\\!\\mathrm{\\hspace{0.10em}e}' +
                            tmp[1][-1])
            else:   # target function values
                if x >= 1:
                    sgn = '+'
                else:
                    sgn = '-'
                tmp2 = tmp[0] + '\\mathrm{\\hspace{0.10em}e}' + sgn + tmp[1][-1]
        else:
            tmp2 = str(format[i]%x)

        tmp2 = '$' + '\\' + fontSize + tmp2 + '$'

        # Print in between separator or end of line separator
        if i != len(vector)-1:
            tmp2 = tmp2 + sep
        else:
            tmp2 = tmp2 + linesep

        # Write to file
        file.write(tmp2)

def postprocessing(data):
    """ Substitutes all entries which are the same as
        the minimum reached value with 'nan'. The minimum
        value appears then only once in the table."""

    last_entry = data[-1]  
    for i in range(2,len(data)+1):
        if data[-i] == last_entry:
            data[-i+1] = numpy.nan
        else:
            break
    return data

def main(argv=None):
    """From a directory which contains the data of the algorithms
       generates tables showing the minimum reached target value and the
       median reached target value for all algorithms will be determined
       for all dimensions and functions.

       Input parameter:
       argv - list of strings containing options and arguments. If not given,
              sys.argv is accessed. The first argument is the directory which
              contains the data files.
       flags:
       -h,--help           - displays help
       -d,--dimensions DIM - dimension(s) of interest
       -f,--functions FUN  - function(s) of interest
       --noisefree         - noisefree function set 
       --noisy             - noisy function set
       -v,--verbose        - verbose output
       Either the flag -f FUN or -nf or -n should be set!
    """

    if argv is None:
        argv = sys.argv[1:]
        
    try: 
        opts, args = getopt.getopt(argv, "hvd:f:",["help", "dimensions=","functions=","noisy","noisefree","verbose"])

    except getopt.error, msg:
        raise Usage(msg)

    if not (args):
        usage()
        sys.exit()

    verboseflag = False
    dims = list()
    funcs = list()
    directory = args  # directories which contains data...

    # Process options
    for o, a in opts:
        if o in ("-h","--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--dimensions"):
            try:
                dims.extend(eval(a))
            except TypeError:
                dims.append(int(a))
        elif o in ("-f", "--functions"):
            try:
                funcs.extend(eval(a))
            except TypeError:
                funcs.append(int(a))
        elif o in ("--noisy"):
            funcs = range(101,131)
        elif o in ("--noisefree"):
            funcs = range(1,25)
        elif o in ("-v","--verbose"):
            verboseflag = True
        else:
            assert False, "unhandled option"

    if len(dims) == 0:
        raise ValueError,('No dimension(s) specified!')
    if len(funcs) == 0:
        raise ValueError,('No function(s) specified!')

    # partition data since not all functions can be displayed in 
    # one table
    partition = [1]
    half = len(funcs)
    if half > 12:
        partition.append(2)
        half = int(round(len(funcs)/2))

    # create dataset
    datasetfull = pproc2.DataSetList(directory,verbose = verboseflag)

    # loop over dimension and functions
    for dim in dims:

        # use partition
        for p in partition:

            # create list which contains min and median values across all 
            # algorithms for all functions
            ftarget = list()
        
            for fun in funcs[0+int((p-1)*half):int(p*half)]:
                
                # create list which only contains entries with dimension = dim
                # for function = fun   
                dataset = list()                     
                for elem in datasetfull:        
                    if elem.dim == dim and elem.funcId == fun:
                        dataset.append(elem)
                        datasetfull.remove(elem)
                
                if len(dataset) == 0:
                    raise ValueError, ('No entry found for dim = %g' %dim 
                                         + ' and function = f%g!' %fun)

                # get min and median values 
                tmp = FunTarget(dataset,dim)
                # some post-processing of the data               
                tmp.minFtarget = postprocessing(tmp.minFtarget)
                tmp.medianFtarget = postprocessing(tmp.medianFtarget)
                ftarget.append({'dim':dim,'funcId':fun,'min':tmp.minFtarget,'median':tmp.medianFtarget,'ert':tmp.ert})

            # write data into table
            writeTable(ftarget,dim,p,whichvalue = 'min')
            writeTable(ftarget,dim,p,whichvalue = 'median')

if __name__ == "__main__":
    sys.exit(main())
    
