import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

csrs = [ 'example.com', 'ecc.example.com', 'another-domain.example.com' ]
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

## sadly, we cannot use more complex tests here... :(
