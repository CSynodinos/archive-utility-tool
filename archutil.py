import io
import os
import zipfile
import tarfile
import rarfile
import errno

def custom_warning(msg, *args, **kwargs):
    """Custom warning message. Hides source code.

    Args:
        msg ([type]: str): Warning message.

    Returns:
        [type]: The warning message.
    """
    return 'Warning: ' + str(msg) + '\n'
import warnings
warnings.formatwarning = custom_warning

from tqdm import tqdm


def _format_check(*args, fmtype):
    """Checks for variable/s type. Helper to _typecheck.
    Args:
        * `*args` ([type]: any): Input variable/s to check.
        * `fmtype` ([type]: any): Type of variable to check.
    Raises:
        TypeError: When type of variable is != to `fmtype`
    """
    for n in args:
        a = type(n).__name__
        if not isinstance(n, fmtype):
            raise TypeError(f'{n} must be of type {fmtype.__name__} not a type {a}')

class archive:
    def __init__(self, __inp__, fl = None, dest = os.getcwd()):
        self.__inp__ = __inp__
        if not os.path.isfile(__inp__):
            raise ValueError('__inp__ must be a path to a file.')

        self.fl = fl
        self.dest = dest

    class _FileObject(io.FileIO):
        def __init__(self, path, flinp, *args, **kwargs):
            """Gets total size of file object."""
            
            self._total_size = os.path.getsize(path)
            self.flinp = flinp
            io.FileIO.__init__(self, path, *args, **kwargs)

        def read(self, size):
            """Reads the current position of the object and prints to stdout if `display` = True.

            Returns:
                [type]: `bytes`: ByteStream of file object.
            """

            if isinstance(self.flinp, type(None)): 
                print("Extracting all files: %d%%" %((self.tell()*100)/self._total_size), end = "\r") # tell() returns the current position of the object. Allows for tracking
                                                                                                        # the extraction progress.
            elif isinstance(self.flinp, str):   # When single file is chosen.
                print("Extracting %s: %d%%" %(self.flinp, ((self.tell()*100)/self._total_size)), end = "\r")
            else:
                print("Extracting %d files: %d%%" %(len(self.flinp), ((self.tell()*100)/self._total_size)), end = "\r")
            return io.FileIO.read(self, size)

    @staticmethod
    def custom_formatwarning(msg, *args, **kwargs):
    # ignore everything except the message
        return str(msg) + '\n'

    @staticmethod
    def chk_opt(inparc, inpfl, gnames):   # check if selected files exist in the archive.
        
        if not [x for x in gnames if x in inpfl]:
            raise KeyError(f'None of the {len(inpfl)} requested files for extraction found in the {(inparc)} archive. Extraction failed.')
        incorrect_opt = list(set(inpfl) - set(gnames))

        if len(incorrect_opt) >= 1:
            for i in incorrect_opt:
                warnings.warn(f"Selected file {i} could not be found. File {i} will be ignored.", stacklevel = 0)
                if i in inpfl:
                    inpfl.remove(i)
            return list(inpfl)
        else:
            return list(inpfl)

    def decompress(self):

        supp_ext = (".zip", ".rar", ".tar.xz", ".tar.gz", ".tar.bz", ".tar")
        zipexts = (".zip")
        tarexts = (".tar.xz", ".tar.gz", ".tar.bz", ".tar")

        if not self.__inp__.endswith(supp_ext):
            raise OSError(f"Compression type: {os.path.splitext(self.__inp__)[1]} is currently not supported.")

        if self.__inp__.endswith(zipexts): # Checks if compression is .zip
            with zipfile.ZipFile(self.__inp__) as zf:
                for member in tqdm(zf.infolist(), desc='Extracting files'):
                    try:
                        zf.extract(member, path = self.dest)
                    except zipfile.error as e:
                        pass

        elif self.__inp__.endswith(".rar"):    # Checks if compression is .rar
            rar = rarfile.open(fileobj = archive._FileObject(self.__inp__))    # rarfile.open opens the file contained in the FileObject class.
            
            rar.extractall(path = self.dest) # File is extracted in the self.dest subdirectory.
            
            rar.close() # File is closed.

        elif self.__inp__.endswith(tarexts):
            if isinstance(self.fl, type(None)): # No specific file is selected for extraction, extract whole archive.
                tar = tarfile.open(fileobj = archive._FileObject(self.__inp__, flinp = self.fl))
                tar.extractall(path = self.dest)
                tar.close()

            else:
                if isinstance(self.fl, str): # Single file to decompress from archive.
                    tar = tarfile.open(fileobj = archive._FileObject(self.__inp__, flinp = self.fl))
                    membername = tar.getnames()
                    if self.fl in membername:
                        member = tar.getmember(name = self.fl)
                        tar.extract(member)
                    else:
                        raise KeyError(f'The requested file {self.fl} was not found in the {(self.__inp__)} archive. Extraction failed.')

                elif isinstance(self.fl, list):     # A list of files to decompress.
                    tarcheck = tarfile.open(self.__inp__)   # Temporarily open the file to get the names of the members and check if any of the requested files exist.
                    compfiles = tarcheck.getnames()
                    tarcheck.close()

                    fls = self.chk_opt(inparc = self.__inp__, inpfl = self.fl, gnames = compfiles)

                    tar = tarfile.open(fileobj = archive._FileObject(self.__inp__, flinp = self.fl))
                    for i in fls:   # Iterate the appended elements.
                        try:
                            if [n for n in compfiles if n in fls]:  # decompress only if the iterable is an element in the getnames() list.
                                member = tar.getmember(name = i)
                                tar.extract(member)
                        except: # if iterable not in getnames(), continue to next iterable.
                            continue

                else:
                    raise TypeError('fl input parameter must be of type string if you wish to decompress one file, type list if you wish ' 
                                    + 'to decompress multiple selected files or None if you wish to decompress the entire archive, '
                                    f'not of type {type(self.fl).__name__}.')

    def compress():
        pass

if __name__ == "__main__":
    x = archive(__inp__ = r"E:\Documents\Python_Scripts\archive utility tool\Documents.tar", fl = ['test.txt', 'bed.docx', 'Presentation TOK.docx', 'yomama'], dest = r"E:\Documents\Python_Scripts\archive utility tool\output")
    x.decompress()