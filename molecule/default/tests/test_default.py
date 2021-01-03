import os
import testinfra.utils.ansible_runner

import cryptography
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import ExtensionOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from typing import cast


testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

csrs = { 'example.com':                ['foo.example.com'],
         'ecc.example.com':            ['secp.example.com', 'ecc.example.com'],
         'another-domain.example.com': ['another-domain-abc.example.com',
                                        'another-domain-def.example.com',
                                        'another-domain-ghi.example.com',
                                        'another-domain-jkl.example.com',
                                        'another-domain-mno.example.com']
        }
keys =[{ "name": "example.com",                "type": "RSA", "size": 4096 },
       { "name": "ecc.example.com",            "type": "ECC", "size": 384, "curve": "secp384r1" },
       { "name": "another-domain.example.com", "type": "ECC", "size": 256, "curve": "secp256r1" }
]
base_path = '/etc/letsencrypt'


def test_sanity_check(host):
    f = host.file('/etc/passwd')
    assert f.exists
    assert f.is_file


def test_key_and_csr_present(host):
    for csr in csrs:
        for t in [ 'domain.key', 'domain.csr' ]:
            f = host.file('{0}/{1}/{2}'.format(base_path, csr, t))
            assert f.exists
            assert f.is_file

def test_private_keys(host):
    for k in keys:
        key_file_data = host.file('{0}/{1}/domain.key'.format(base_path, k["name"])).content
        priv_key = load_pem_private_key(key_file_data, None, default_backend())

        if k["type"] == "ECC":
            assert isinstance(priv_key, cryptography.hazmat.primitives.asymmetric.ec.EllipticCurvePrivateKey)
            assert priv_key.curve.name == k["curve"]
        elif k["type"] == "RSA":
            assert isinstance(priv_key, cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey)

        assert priv_key.key_size == k["size"]


def test_csr_SANs(host):
    for csr in csrs:
        csr_data = host.file('{0}/{1}/domain.csr'.format(base_path, csr)).content
        csr_loaded = x509.load_pem_x509_csr(csr_data, default_backend())

        san = csr_loaded.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        san_values = cast(x509.SubjectAlternativeName, san.value)
        subj_alt_names = san_values.get_values_for_type(x509.DNSName)
        for n in csrs[csr]:
            assert n in subj_alt_names

