# This module implements the base classes for proteins and
# nucleic acid chains.
#
# Written by Konrad Hinsen
#

"""
Base classes for proteins and nucleic acids
"""

from MMTK import Bonds, ChemicalObjects, Collections, Database, PDB
import Scientific.IO.PDB

class Residue(ChemicalObjects.Group):

    """
    Base class for aminoacid and nucleic acid residues
    """

    def __setstate__(self, state):
        self.__dict__.update(state)
        try:
            self.model = self.hydrogens
        except AttributeError:
            pass
        self._init()

    def _init(self):
        # construct PDB map and alternative names
        type = self.type
        if not hasattr(type, 'pdbmap'):
            pdb_dict = {}
            type.pdbmap = [(type.symbol, pdb_dict)]
            offset = 0
            for g in type.groups:
                for name, atom in g.pdbmap[0][1].items():
                    pdb_dict[name] = Database.AtomReference(atom.number + \
                                                            offset)
                offset = offset + len(g.atoms)
        if not hasattr(type, 'pdb_alternative'):
            alt_dict = {}
            for g in type.groups:
                if hasattr(g, 'pdb_alternative'):
                    for key, value in g.pdb_alternative.items():
                        alt_dict[key] = value
            setattr(type, 'pdb_alternative', alt_dict)

    def _residueThroughLinkAtom(self, link_atom):
        if link_atom is None:
            return None
        levels = 0
        obj = link_atom
        while obj is not None and obj != self:
            obj = obj.parent
            levels += 1
        for atom in link_atom.bondedTo():
            if atom.parent is not link_atom.parent:
                obj = atom
                while levels > 0:
                    obj = obj.parent
                    levels -= 1
                return obj
        return None

    def precedingResidue(self):
        """
        :returns the preceding residue in the chain
        """
        return self._residueThroughLinkAtom(self.chain_links[0])

    def nextResidue(self):
        """
        :returns the next residue in the chain
        """
        return self._residueThroughLinkAtom(self.chain_links[1])

class ResidueChain(ChemicalObjects.Molecule):

    """
    Chain of residues

    Base class for peptide chains and nucleotide chains
    """
    
    is_chain = 1

    def _setupChain(self, circular, properties, conf):
        self.atoms = []
        self.bonds = []
        for g in self.groups:
            self.atoms.extend(g.atoms)
            self.bonds.extend(g.bonds)
        for i in range(len(self.groups)-1):
            link1 = self.groups[i].chain_links[1]
            link2 = self.groups[i+1].chain_links[0]
            self.bonds.append(Bonds.Bond((link1, link2)))
        if circular:
            link1 = self.groups[-1].chain_links[1]
            link2 = self.groups[0].chain_links[0]
            self.bonds.append(Bonds.Bond((link1, link2)))
        self.bonds = Bonds.BondList(self.bonds)
        self.parent = None
        self.type = None
        self.configurations = {}
        try:
            self.name = properties['name']
            del properties['name']
        except KeyError:
            self.name = ''
        if conf:
            conf.applyTo(self)
        try:
            self.translateTo(properties['position'])
            del properties['position']
        except KeyError:
            pass
        self.addProperties(properties)

    def __len__(self):
        return len(self.groups)

    def __getitem__(self, item):
        return self.groups[item]

    def __setitem__(self, item, value):
        self.replaceResidue(self.groups[item], value)

    def residuesOfType(self, *types):
        """
        :param types: residue type codes
        :type types: str
        :returns: a collection that contains all residues whose type
                  (residue code) is contained in types
        :rtype: :class:`~MMTK.Collections.Collection`
        """
        types = [t.lower() for t in types]
        rlist = [r for r in self.groups if r.type.symbol.lower() in types]
        return Collections.Collection(rlist)

    def residues(self):
        """
        :returns: a collection containing all residues
        :rtype: :class:`~MMTK.Collections.Collection`
        """
        return Collections.Collection(self.groups)

    def sequence(self):
        """
        :returns: the residue sequence as a list of residue codes
        :rtype: list of str
        """
        return [r.type.symbol.lower() for r in self.groups]

#
# Find the full name of a residue
#
def _fullName(residue):
    residue = residue.lower()
    try:
        return _aa_residue_names[residue]
    except KeyError:
        return _na_residue_names[residue]

_aa_residue_names = {'ala': 'alanine',          'a': 'alanine',
                     'arg': 'arginine',         'r': 'arginine',
                     'asn': 'asparagine',       'n': 'asparagine',
                     'asp': 'aspartic_acid',    'd': 'aspartic_acid',
                     'cys': 'cysteine',         'c': 'cysteine',
                     'gln': 'glutamine',        'q': 'glutamine',
                     'glu': 'glutamic_acid',    'e': 'glutamic_acid',
                     'gly': 'glycine',          'g': 'glycine',
                     'his': 'histidine',        'h': 'histidine',
                     'ile': 'isoleucine',       'i': 'isoleucine',
                     'leu': 'leucine',          'l': 'leucine',
                     'lys': 'lysine',           'k': 'lysine',
                     'met': 'methionine',       'm': 'methionine',
                     'phe': 'phenylalanine',    'f': 'phenylalanine',
                     'pro': 'proline',          'p': 'proline',
                     'ser': 'serine',           's': 'serine',
                     'thr': 'threonine',        't': 'threonine',
                     'trp': 'tryptophan',       'w': 'tryptophan',
                     'tyr': 'tyrosine',         'y': 'tyrosine',
                     'val': 'valine',           'v': 'valine',
                     'cyx': 'cystine_ss',
                     'cym': 'cysteine_with_negative_charge',
                     'app': 'aspartic_acid_neutral',
                     'glp': 'glutamic_acid_neutral',
                     'hsd': 'histidine_deltah', 'hse': 'histidine_epsilonh',
                     'hsp': 'histidine_plus',
                     'hid': 'histidine_deltah', 'hie': 'histidine_epsilonh',
                     'hip': 'histidine_plus',
                     'lyp': 'lysine_neutral',
                     'pt2': 'phosphotyrosine_2',
                     'ace': 'ace_beginning',    'nme': 'nmethyl',
                     'nhe': 'amide',
                     }

_na_residue_names = {'da': 'd-adenosine',
                     'da5': 'd-adenosine_5ter',
                     'da3': 'd-adenosine_3ter',
                     'dan': 'd-adenosine_5ter_3ter',
                     'dc': 'd-cytosine',
                     'dc5': 'd-cytosine_5ter',
                     'dc3': 'd-cytosine_3ter',
                     'dcn': 'd-cytosine_5ter_3ter',
                     'dg': 'd-guanosine',
                     'dg5': 'd-guanosine_5ter',
                     'dg3': 'd-guanosine_3ter',
                     'dgn': 'd-guanosine_5ter_3ter',
                     'dt': 'd-thymine',
                     'dt5': 'd-thymine_5ter',
                     'dt3': 'd-thymine_3ter',
                     'dtn': 'd-thymine_5ter_3ter',
                     'ra': 'r-adenosine',
                     'ra5': 'r-adenosine_5ter',
                     'ra3': 'r-adenosine_3ter',
                     'ran': 'r-adenosine_5ter_3ter',
                     'rc': 'r-cytosine',
                     'rc5': 'r-cytosine_5ter',
                     'rc3': 'r-cytosine_3ter',
                     'rcn': 'r-cytosine_5ter_3ter',
                     'rg': 'r-guanosine',
                     'rg5': 'r-guanosine_5ter',
                     'rg3': 'r-guanosine_3ter',
                     'rgn': 'r-guanosine_5ter_3ter',
                     'ru': 'r-uracil',
                     'ru5': 'r-uracil_5ter',
                     'ru3': 'r-uracil_3ter',
                     'run': 'r-uracil_5ter_3ter',
                     }

for code in _aa_residue_names:
    if len(code) == 3:
        Scientific.IO.PDB.defineAminoAcidResidue(code)
for code in _na_residue_names:
    Scientific.IO.PDB.defineNucleicAcidResidue(code)

#
# Add a residue to the residue list
#
def defineAminoAcidResidue(full_name, code3, code1 = None):
    """
    Add a non-standard amino acid residue to the internal residue table.
    Once added to the residue table, the new residue can be used
    like any of the standard residues in the creation of peptide chains.

    :param full_name: the name of the group definition in the chemical database
    :type full_name: str
    :param code3: the three-letter residue code
    :type code3: str
    :param code1: an optionel one-letter residue code
    :type code1: str
    """
    code3 = code3.lower()
    if code1 is not None:
        code1 = code1.lower()
    if _aa_residue_names.has_key(code3) or _na_residue_names.has_key(code3):
        raise ValueError("residue name " + code3 + " already used")
    if _aa_residue_names.has_key(code1):
        raise ValueError("residue name " + code1 + " already used")
    _aa_residue_names[code3] = full_name
    if code1 is not None:
        _aa_residue_names[code1] = full_name
    Scientific.IO.PDB.defineAminoAcidResidue(code3)

def defineNucleicAcidResidue(full_name, code):
    """
    Add a non-standard nucleic acid residue to the internal residue table.
    Once added to the residue table, the new residue can be used
    like any of the standard residues in the creation of nucleotide chains.

    :param full_name: the name of the group definition in the chemical database
    :type full_name: str
    :param code: the residue code
    :type code3: str
    """
    code = code.lower()
    if _aa_residue_names.has_key(code) or _na_residue_names.has_key(code):
        raise ValueError("residue name " + code + " already used")
    _na_residue_names[code] = full_name
    if code.startswith('r') or code.startswith('d'):
        Scientific.IO.PDB.defineNucleicAcidResidue(code[1:])
    else:
        Scientific.IO.PDB.defineNucleicAcidResidue(code)
