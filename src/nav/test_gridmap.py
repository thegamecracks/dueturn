from . import gridmap


def test_cardinal_to_vector():
    for NS, y_coord in (('N', -1), ('S', 1)):
        for W_E, x_coord in (('W', -1), ('', 0), ('E', 1)):
            coords = [y_coord, x_coord]
            assert gridmap.cardinal_to_vector(NS + W_E) == coords
            # Test commutativity property by reversing the cardinal
            assert gridmap.cardinal_to_vector(W_E + NS) == coords


def test_reverse_cardinal():
    NS = ('N', 'S')
    W_E = ('W', '', 'E')

    for ns, ns_reverse in zip(NS, reversed(NS)):
        assert gridmap.reverse_cardinal(ns) == ns_reverse
        for w_e, w_e_reverse in zip(W_E, reversed(W_E)):
            assert gridmap.reverse_cardinal(
                ns + w_e
            ) == ns_reverse + w_e_reverse
            # Test commutativity property by reversing the input cardinal
            assert gridmap.reverse_cardinal(
                w_e + ns
            ) == ns_reverse + w_e_reverse
    for w_e, w_e_reverse in zip(W_E, reversed(W_E)):
        if w_e == '':
            continue
        assert gridmap.reverse_cardinal(w_e) == w_e_reverse


def test_vector_to_cardinal():
    for NS, y_coord in (('N', -1), ('S', 1)):
        for W_E, x_coord in (('W', -1), ('', 0), ('E', 1)):
            assert gridmap.vector_to_cardinal(y_coord, x_coord) == NS + W_E
