import _string
import string
import sys

from src import logs

DEFAULT_TEXT_COLOR: str = '{Snorma}{Fcyan}{Bblack}'
# Color of default text (see ColoramaCodes class for colors)
# Can use both Foreground and Background colors.
# To use the terminal's default, set the setting to an empty string.

logger = logs.get_logger()

# Try importing colorama
if 'idlelib.run' in sys.modules:
    # Disable colorama when in IDLE's shell
    cr = None
    logger.info('Running in IDLE; disabled color')
else:
    try:
        import colorama as cr
    except ModuleNotFoundError:
        cr = None
        logger.info('Missing colorama module, color not available')


class ColoramaCodesDisabled:
    'Disabled version of ColoramaCodes.'
    NONE = ''
    # Codes
    # Foreground
    Fblack = NONE
    Fblue  = NONE
    Fcyan  = NONE
    Fgreen = NONE
    Fmagen = NONE
    Fred   = NONE
    Fwhite = NONE
    Fyello = NONE
    FLblac = NONE
    FLblue = NONE
    FLcyan = NONE
    FLgree = NONE
    FLmage = NONE
    FLred  = NONE
    FLwhit = NONE
    FLyell = NONE
    Freset = NONE
    # Background
    Bblack = NONE
    Bblue  = NONE
    Bcyan  = NONE
    Bgreen = NONE
    Bmagen = NONE
    Bred   = NONE
    Bwhite = NONE
    Byello = NONE
    BLblac = NONE
    BLblue = NONE
    BLcyan = NONE
    BLgree = NONE
    BLmage = NONE
    BLred  = NONE
    BLwhit = NONE
    BLyell = NONE
    Breset = NONE
    # Style
    Sreset = NONE
    Sbrigh = NONE
    Sdim   = NONE
    Snorma = NONE
    # Reset all
    RESET_ALL = NONE
    # Shortened Codes
    # Foreground
    Fbk  = NONE
    Fbe  = NONE
    Fcy  = NONE
    Fgr  = NONE
    Fmg  = NONE
    Frd  = NONE
    Fwi  = NONE
    Fyl  = NONE
    FLbk = NONE
    FLbe = NONE
    FLcy = NONE
    FLgr = NONE
    FLmg = NONE
    FLrd = NONE
    FLwi = NONE
    FLyl = NONE
    Fr   = NONE
    # Background
    Bbk  = NONE
    Bbe  = NONE
    Bcy  = NONE
    Bgr  = NONE
    Bmg  = NONE
    Brd  = NONE
    Bwi  = NONE
    Byl  = NONE
    BLbk = NONE
    BLbe = NONE
    BLcy = NONE
    BLgr = NONE
    BLmg = NONE
    BLrd = NONE
    BLwi = NONE
    BLyl = NONE
    Br   = NONE
    # Style
    Sr = NONE
    Sb = NONE
    Sd = NONE
    Sn = NONE
    # Reset All
    RA = NONE
    codes = {
        'Fblack': NONE,
        'Fblue' : NONE,
        'Fcyan' : NONE,
        'Fgreen': NONE,
        'Fmagen': NONE,
        'Fred'  : NONE,
        'Fwhite': NONE,
        'Fyello': NONE,
        'FLblac': NONE,
        'FLblue': NONE,
        'FLcyan': NONE,
        'FLgree': NONE,
        'FLmage': NONE,
        'FLred' : NONE,
        'FLwhit': NONE,
        'FLyell': NONE,
        'Freset': NONE,

        'Bblack': NONE,
        'Bblue' : NONE,
        'Bcyan' : NONE,
        'Bgreen': NONE,
        'Bmagen': NONE,
        'Bred'  : NONE,
        'Bwhite': NONE,
        'Byello': NONE,
        'BLblac': NONE,
        'BLblue': NONE,
        'BLcyan': NONE,
        'BLgree': NONE,
        'BLmage': NONE,
        'BLred' : NONE,
        'BLwhit': NONE,
        'BLyell': NONE,
        'Breset': NONE,

        'Sreset': NONE,
        'Sbrigh': NONE,
        'Sdim'  : NONE,
        'Snorma': NONE,

        'RESET_ALL': NONE,

        'Fbk' : NONE,
        'Fbe' : NONE,
        'Fcy' : NONE,
        'Fgr' : NONE,
        'Fmg' : NONE,
        'Frd' : NONE,
        'Fwi' : NONE,
        'Fyl' : NONE,
        'FLbk': NONE,
        'FLbe': NONE,
        'FLcy': NONE,
        'FLgr': NONE,
        'FLmg': NONE,
        'FLrd': NONE,
        'FLwi': NONE,
        'FLyl': NONE,
        'Fr'  : NONE,

        'Bbk' : NONE,
        'Bbe' : NONE,
        'Bcy' : NONE,
        'Bgr' : NONE,
        'Bmg' : NONE,
        'Brd' : NONE,
        'Bwi' : NONE,
        'Byl' : NONE,
        'BLbk': NONE,
        'BLbe': NONE,
        'BLcy': NONE,
        'BLgr': NONE,
        'BLmg': NONE,
        'BLrd': NONE,
        'BLwi': NONE,
        'BLyl': NONE,
        'Br'  : NONE,

        'Sr': NONE,
        'Sb': NONE,
        'Sd': NONE,
        'Sn': NONE,

        'RA': NONE
    }


if cr:
    class ColoramaCodes:
        'A class storing colorama codes for colored printing to the terminal.'
        # Codes
        # Foreground
        Fblack = cr.Fore.BLACK
        Fblue  = cr.Fore.BLUE
        Fcyan  = cr.Fore.CYAN
        Fgreen = cr.Fore.GREEN
        Fmagen = cr.Fore.MAGENTA
        Fred   = cr.Fore.RED
        Fwhite = cr.Fore.WHITE
        Fyello = cr.Fore.YELLOW
        FLblac = cr.Fore.LIGHTBLACK_EX
        FLblue = cr.Fore.LIGHTBLUE_EX
        FLcyan = cr.Fore.LIGHTCYAN_EX
        FLgree = cr.Fore.LIGHTGREEN_EX
        FLmage = cr.Fore.LIGHTMAGENTA_EX
        FLred  = cr.Fore.LIGHTRED_EX
        FLwhit = cr.Fore.LIGHTWHITE_EX
        FLyell = cr.Fore.LIGHTYELLOW_EX
        Freset = cr.Fore.RESET

        # Background
        Bblack = cr.Back.BLACK
        Bblue  = cr.Back.BLUE
        Bcyan  = cr.Back.CYAN
        Bgreen = cr.Back.GREEN
        Bmagen = cr.Back.MAGENTA
        Bred   = cr.Back.RED
        Bwhite = cr.Back.WHITE
        Byello = cr.Back.YELLOW
        BLblac = cr.Back.LIGHTBLACK_EX
        BLblue = cr.Back.LIGHTBLUE_EX
        BLcyan = cr.Back.LIGHTCYAN_EX
        BLgree = cr.Back.LIGHTGREEN_EX
        BLmage = cr.Back.LIGHTMAGENTA_EX
        BLred  = cr.Back.LIGHTRED_EX
        BLwhit = cr.Back.LIGHTWHITE_EX
        BLyell = cr.Back.LIGHTYELLOW_EX
        Breset = cr.Back.RESET

        # Style
        # "Sreset" would be the default that the terminal uses,
        # however I am only aware of Windows's default, which is bright
        Sreset = cr.Style.BRIGHT
        Sbrigh = cr.Style.BRIGHT
        Sdim   = cr.Style.DIM
        Snorma = cr.Style.NORMAL

        # Reset all
        RESET_ALL = cr.Style.RESET_ALL

        # Shortened Codes
        # Foreground
        Fbk  = Fblack
        Fbu  = Fblue
        Fcy  = Fcyan
        Fgr  = Fgreen
        Fmg  = Fmagen
        Frd  = Fred
        Fwi  = Fwhite
        Fyl  = Fyello
        FLbk = FLblac
        FLbu = FLblue
        FLcy = FLcyan
        FLgr = FLgree
        FLmg = FLmage
        FLrd = FLred
        FLwi = FLwhit
        FLyl = FLyell
        Fr   = Freset

        # Background
        Bbk  = Bblack
        Bbu  = Bblue
        Bcy  = Bcyan
        Bgr  = Bgreen
        Bmg  = Bmagen
        Brd  = Bred
        Bwi  = Bwhite
        Byl  = Byello
        BLbk = BLblac
        BLbu = BLblue
        BLcy = BLcyan
        BLgr = BLgree
        BLmg = BLmage
        BLrd = BLred
        BLwi = BLwhit
        BLyl = BLyell
        Br   = Breset

        # Style
        Sr = Sreset
        Sb = Sbrigh
        Sd = Sdim
        Sn = Snorma

        # Reset All
        RA = RESET_ALL

        codes = {
            'Fblack': Fblack,
            'Fblue' : Fblue,
            'Fcyan' : Fcyan,
            'Fgreen': Fgreen,
            'Fmagen': Fmagen,
            'Fred'  : Fred,
            'Fwhite': Fwhite,
            'Fyello': Fyello,
            'FLblac': FLblac,
            'FLblue': FLblue,
            'FLcyan': FLcyan,
            'FLgree': FLgree,
            'FLmage': FLmage,
            'FLred' : FLred,
            'FLwhit': FLwhit,
            'FLyell': FLyell,
            'Freset': Freset,

            'Bblack': Bblack,
            'Bblue' : Bblue,
            'Bcyan' : Bcyan,
            'Bgreen': Bgreen,
            'Bmagen': Bmagen,
            'Bred'  : Bred,
            'Bwhite': Bwhite,
            'Byello': Byello,
            'BLblac': BLblac,
            'BLblue': BLblue,
            'BLcyan': BLcyan,
            'BLgree': BLgree,
            'BLmage': BLmage,
            'BLred' : BLred,
            'BLwhit': BLwhit,
            'BLyell': BLyell,
            'Breset': Breset,

            'Sreset': Sreset,
            'Sbrigh': Sbrigh,
            'Sdim'  : Sdim,
            'Snorma': Snorma,

            'RESET_ALL': RESET_ALL,

            'Fbk' : Fblack,
            'Fbu' : Fblue,
            'Fcy' : Fcyan,
            'Fgr' : Fgreen,
            'Fmg' : Fmagen,
            'Frd' : Fred,
            'Fwi' : Fwhite,
            'Fyl' : Fyello,
            'FLbk': FLblac,
            'FLbu': FLblue,
            'FLcy': FLcyan,
            'FLgr': FLgree,
            'FLmg': FLmage,
            'FLrd': FLred,
            'FLwi': FLwhit,
            'FLyl': FLyell,
            'Fr'  : Freset,

            'Bbk' : Bblack,
            'Bbu' : Bblue,
            'Bcy' : Bcyan,
            'Bgr' : Bgreen,
            'Bmg' : Bmagen,
            'Brd' : Bred,
            'Bwi' : Bwhite,
            'Byl' : Byello,
            'BLbk': BLblac,
            'BLbu': BLblue,
            'BLcy': BLcyan,
            'BLgr': BLgree,
            'BLmg': BLmage,
            'BLrd': BLred,
            'BLwi': BLwhit,
            'BLyl': BLyell,
            'Br'  : Breset,

            'Sr': Sr,
            'Sb': Sb,
            'Sd': Sd,
            'Sn': Sn,

            'RA': RA
        }
else:
    class ColoramaCodes(ColoramaCodesDisabled):
        'Disabled version of ColoramaCodes since colorama is not available.'


class EvalFormatter(string.Formatter):
    """Copied from string.py's Formatter class, modified to evaluate fields.

    This will allow f-string like formatting.

    Of course, this is a security risk, but for the purposes of
    a game meant to run offline, that security risk is being ignored.

    """

    def get_field(self, field_name, args, kwargs):
        first, _ = _string.formatter_field_name_split(field_name)

        obj = eval(field_name, kwargs)

        return obj, first


def format_color(
        s: str, *, namespace=None,
        prefixBraces=1, escape_dollar=True,
        no_color=False) -> str:
    """Format the given string with all the codes in ColoramaCodes.

    Note:
        `string.Formatter` is used to format color codes, so looking at that
        documentation may help with creating strings for this. For example:
            "$$ is an escape; it is replaced with a single $."

    Args:
        namespace (dict): Format the string with a dictionary if available.
            This happens after colors are formatted.
        prefixBraces (int):
            If 0, do nothing about left braces.
            If 1, prefix all left braces ({) with $ for
            partial formatting and after safely substituting color codes,
            replace all "${" in the string with "{".
            This option is for maintaining compatibility with the
            current strings and using the same semantics without changing them
            to accommodate the different format of
            string.Template.safe_substitute().
        escape_dollar (bool):
            If True, turn all "$" into "$$" to escape them from
            string.Template's substitution.
            When the input string is already properly made for
            safe_substitute(), enabling this will conflict as it will not
            distinguish dollar signs meant for identifiers such as in "${foo}".
            Escaping dollar signs happens before braces are prefixed with $.
        no_color (bool):
            Remove all code placeholders instead of substituting
            their corresponding codes.

    """
    if namespace is None:
        namespace = {}
    if escape_dollar:
        s = s.replace('$', '$$')
    if prefixBraces == 1:
        s = s.replace('{', '${')
    codes = ColoramaCodesDisabled if no_color else ColoramaCodes
    s = string.Template(s).safe_substitute(codes.codes)
    if prefixBraces == 1:
        s = s.replace('${', '{')
    s = EvalFormatter().format(s, **namespace)
    return s


def input_color(*values, end=None, **kwargs):
    print_color(*values, end='', **kwargs)

    input_ = input()

    if end is None:
        end = ColoramaCodes.RESET_ALL
    print_color(end=end)

    return input_


def print_color(
        *values,
        do_not_format=False,
        sep=' ', end=None, file=None, flush=False,
        **kwargs) -> None:
    """Print a string with color code substitutions.

    Format the given string with all the codes in ColoramaCodes
    and append a RESET_ALL code at the end of the string, then print it
    with other arguments passed into print().

    Args:
        *values (str): Strings to format and print.
        do_not_format (bool): Delete color code substitutions
            instead of printing them.
        sep (str): Passed through to print().
        end (Optional[str]): The string printed at the end.
            If None, defaults to codes.RESET_ALL + '\n'.
        file (Optional[_io.TextIOWrapper]): Passed through to print().
        flush (bool): Passed through to print().
        **kwargs: Other keyword arguments are passed into print().

    """
    if end is None:
        end = ColoramaCodes.RESET_ALL + '\n'

    if do_not_format:
        msg = sep.join([str(v) for v in values])
    else:
        msg = format_color(sep.join([str(v) for v in values]), **kwargs)

    # Need to make `file` not be included because passing in sys.stdout
    # will bypass colorama's wrapper
    print_kwargs = {'end': end, 'flush': flush}
    if file is not None:
        print_kwargs['file'] = file

    print(msg, **print_kwargs)


def update_colorama_reset(new_reset=None, auto_reset=False):
    """Update the current ColoramaCodes.RESET_ALL code with new_reset.

    `DEFAULT_TEXT_COLOR` will be changed to `new_reset`.

    By default, the reset code is not automatically printed, meaning
    the reset must be printed manually. This perserves any current
    colors that are active.
    To automatically print it, set the `auto_reset` to True.

    Args:
        new_reset (Optional[str]): The new reset code to format and use.
            If None, will use DEFAULT_TEXT_COLOR.
        auto_reset (bool): Print the reset code after finishing.

    """
    if cr:
        if new_reset is not None:
            global DEFAULT_TEXT_COLOR
            DEFAULT_TEXT_COLOR = new_reset
        new_reset = cr.Style.RESET_ALL + format_color(
            DEFAULT_TEXT_COLOR)
        ColoramaCodes.RESET_ALL = new_reset
        ColoramaCodes.RA = new_reset
        ColoramaCodes.codes['RESET_ALL'] = new_reset
        ColoramaCodes.codes['RA'] = new_reset
        if auto_reset:
            print(new_reset, end='')


def colorio_setup():
    """Initialize colorama if available."""
    if cr:
        cr.init()
        update_colorama_reset()
        # Clear screen
        print_color(ColoramaCodes.RESET_ALL + '\x1b[2J', end='')
