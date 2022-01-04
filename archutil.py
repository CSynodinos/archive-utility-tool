import io
import os
import zipfile
import tarfile
import rarfile
import errno
from pathlib import Path
from tqdm import tqdm

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
    def __init__(self, __inp__, display = True, fl = None, dest = os.getcwd()):
        self.__inp__ = __inp__
        if not Path(self.__inp__).exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.__inp__)

        self.display = display
        if not isinstance(display, bool):
            raise ValueError('display must be of type: Boolean.')

        if not os.path.isfile(__inp__):
            raise ValueError('__inp__ must be a path to a file.')

        self.fl = fl
        self.dest = dest

    class _FileObject(io.FileIO):
        """Internal class for creating an IO object to check extraction progression for tarfile."""

        def __init__(self, path, displ, flinp, *args, **kwargs):
            """Gets total size of file object."""

            self.displ = displ
            self._total_size = os.path.getsize(path)
            self.flinp = flinp
            io.FileIO.__init__(self, path, *args, **kwargs)

        def read(self, size):
            """Reads the current position of the object and prints to stdout if `display` = True.

            Returns:
                [type]: `bytes`: ByteStream of file object.
            """

            if self.displ == True:
                if isinstance(self.flinp, type(None)): 
                    print("Extracting all files: %d%%" %((self.tell()*100) / self._total_size), end = "\r") # tell() returns the current position of the object. Allows for tracking
                                                                                                            # the extraction progress.

                elif isinstance(self.flinp, str):   # When single file is chosen or when list of strings is being iterated.
                    print("Extracting %s: %d%%" %(self.flinp, ((self.tell()*100) / self._total_size)), end = "\r")

                elif isinstance(self.flinp, list):
                    print("Extracting %d files: %d%%" %(len(self.flinp), ((self.tell()*100) / self._total_size)), end = "\r")

            elif self.displ == False:
                pass

            return io.FileIO.read(self, size)

    @staticmethod
    def chk_opt(inparc, inpfl, gnames):   # check if selected files exist in the archive.
        """Check if selected files for extraction exist in the archive.

        Args:
            * `inparc` ([type]: `str`): Path to archive for extraction.
            * `inpfl` ([type]: `list`): List of files to extract.
            * `gnames` ([type]: `list`): List of all files in the archive.

        Raises:
            * `KeyError`: Raised when none of the selected files are present in the archive.
            * `Warning`: When one or more of the selected files are not present in the archive. 

        Returns:
            [type]: `list`: The list of the selected files that are present in the archive.  
        """

        if not [x for x in gnames if x in inpfl]:   # None of the selected files are present in the archive.
            raise KeyError(f'None of the {len(inpfl)} requested files for extraction found in the {(inparc).__name__} archive. Extraction failed.')
        incorrect_opt = list(set(inpfl) - set(gnames))

        if len(incorrect_opt) >= 1: # Not possible to be 0 because KeyError would have initiated.
            for i in incorrect_opt:
                warnings.warn(f"Selected file {i} could not be found. File {i} will be ignored.", stacklevel = 0)
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
            rar = rarfile.open(fileobj = archive._FileObject(self.__inp__, displ= self.display))    # rarfile.open opens the file contained in the FileObject class.
            
            rar.extractall(path = self.dest) # File is extracted in the self.dest subdirectory.
            
            rar.close() # File is closed.

        elif self.__inp__.endswith(tarexts):
            if isinstance(self.fl, type(None)): # No specific file is selected for extraction, extract whole archive.
                tar = tarfile.open(fileobj = archive._FileObject(self.__inp__, displ= self.display, flinp = self.fl))
                tar.extractall(path = self.dest)
                tar.close()

            else:
                if isinstance(self.fl, str): # Single file to decompress from archive.
                    tar = tarfile.open(fileobj = archive._FileObject(self.__inp__, displ= self.display, flinp = self.fl))
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

                    tar = tarfile.open(fileobj = archive._FileObject(self.__inp__, displ= self.display, flinp = self.fl))
                    for i in fls:   # Iterate the appended elements.
                        member = tar.getmember(name = i)
                        tar.extract(member)
                    tar.close()

                else:
                    raise TypeError('fl input parameter must be of type string if you wish to decompress one file, type list if you wish ' 
                                    'to decompress multiple files or None if you wish to decompress the entire archive, '
                                    f'not of type {type(self.fl).__name__}.')

    def compress():
        pass

if __name__ == "__main__":
    x = archive(__inp__ = r"E:\Documents\Python_Scripts\archive utility tool\Documents.tar", fl = ['test.txt', 'bed.docx'], display = True, dest = r"E:\Documents\Python_Scripts\archive utility tool\output")
    x.decompress()