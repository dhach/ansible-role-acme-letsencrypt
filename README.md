# acme-letsencrypt

![CI](https://github.com/dhach/ansible-role-acme-letsencrypt/workflows/CI/badge.svg)
![release](https://github.com/dhach/ansible-role-acme-letsencrypt/workflows/release/badge.svg)
[![Ansible Galaxy](https://img.shields.io/badge/Ansible--Galaxy-dhach.acme__letsencrypt-blue)](https://galaxy.ansible.com/dhach/acme_letsencrypt)

## Overview

This is a pure-Ansible role to achieve the following:

* Create ECC or RSA private keys
* generate certificate signing requests (for multiple domains)
* Send the request to Let's Encrypt or another ACME Provider of your choice
* Install all files under a deterministic location

I wrote this role to have a way to get Let's Encrypt certificates without having to rely on any third-party tooling (like certbot, acme-tiny, acme.sh, etc.) and have more control over what's going on.

Currently, only HTTP Challenge type is supported.

Since this is just an Ansible role, it does not handle automatic certificate renewal. To achieve this, you can either run this role periodically from your CI/CD pipeline or have it operate in Ansible Pull-mode with a crontab.

## Ansible Version

This role, starting with release 2.0.0, is only guaranteed to be compatible with Ansible >=2.10.

If you need compatibility with <2.10 (aka "pre-collections"), use any release with a 1.x.x. tag.

## Requirements

On target host:

* openssl

## Example playbooks

Using a secp384r1 ECC Key for a SAN certificate (multiple domains).

```YAML
- name: "Get certificates for webserver01"
  hosts: webserver01
  become: true
  roles:
    - dhach.acme_letsencrypt
  vars:
    le_base_directory: /etc/letsencrypt
    le_certificates:
      - name: ecc.example.com
        domains:
          - secp.example.com
          - ecc.example.com
        key:
          curve: secp384r1
```

Now use a secp256r1 key, have it forcefully recreated, and then issue the request against Let's Encrypt production validation server:

```YAML
- name: "Get certificates for webserver02"
  hosts: webserver02
  become: true
  roles:
    - dhach.acme_letsencrypt
  vars:
    le_acme_directory: https://acme-v02.api.letsencrypt.org/directory
    le_certificates:
      - name: another-domain.example.com
        domains:
          - another-domain-abc.example.com
          - another-domain-def.example.com
          - another-domain-ghi.example.com
          - another-domain-jkl.example.com
          - another-domain-mno.example.com
        ssl:
          type: ECC
          curve: secp256r1
          renew: true
```

Or use RSA keys to get one certificate each for domain:

```YAML
- name: "Get certificates for webserver03"
  hosts: webserver03
  become: true
  roles:
    - dhach.acme_letsencrypt
  vars:
    le_certificates:
      - name: example.com
        domains:
          - foo.example.com
        key:
          type: RSA
          size: 4096
      - name: more.example.com
        domains:
          - bar.example.com
        key:
           type: RSA
           size: 4096
```

## Where to find the files

All generated keys, certificate requests and subsequent certificates can be found under the value of `{{ le_base_directory }}/{{ le_certificates['name'] }}`.

E.g, if you specify a `name` of 'example.com', and `le_base_directory` is set to '/etc/letsencrypt/', the result would be:

```none
/etc/letsencrypt/example.com/
├── domain.csr
├── domain.key
├── domain.pem
├── fullchain.pem
└── intermediate.pem
```

## How to configure your webserver

ACME servers require you to answer a challenge by putting a file with a specific name and content into a pre-defined Path your webserver serves via HTTP.

Your webserver has to serve the location */.well-known/acme-challenge* with the contents of the following directoy: `{{ le_base_directory }}/.well-known/acme-challenge/`.

Examples if using the default value for `le_base_directory`:

**Nginx**:

```Nginx
location /.well-known/acme-challenge {
    alias /etc/letsencrypt/.well-known/acme-challenge/;

}
```

**Apache**:

```ApacheConf
Alias /.well-known/acme-challenge/ "/etc/letsencrypt/.well-known/acme-challenge/"
<Directory "/etc/letsencrypt/.well-known/acme-challenge/">
    AllowOverride None
    Options MultiViews Indexes SymLinksIfOwnerMatch IncludesNoExec
    Require method GET POST OPTIONS
</Directory>
```

## Role Variables and defaults

All defined variables are listed below, with their respective default variables given.

### Certificate requests

You can control for which domains the certificate should be requested. Also, you have the option to specify details regarding key generation. The options slightly differ between RSA and ECC keys.

All certificate requests are constructed as SAN (SubjectAltName) requests.

**ECC**:

```YAML
le_certificates:
  - name: example.com  # essentially an internal identifier and where to save the file
    domains:  # a list of domains you want the certificate to be issued for
      - foo.example.com
      - bar.example.com
    key:  # details for the private key, if one is to be generated
      type: ECC  # (mandatory) Supported types: ECC, RSA
      curve: secp384r1  # (optional | default: secp384r1) Curve for ECC key (no effect on RSA keys).
      renew: false  # (optional | default: false) Whether to forceufully recreate the key. Will always keep a backup
```

**RSA**:

```YAML
le_certificates:
  - name: example.com  # essentially an internal identifier and where to save the file
    domains:  # a list of domains you want the certificate to be issued for
      - foo.example.com
      - bar.example.com
    key:  # details for the private key, if one is to be generated
      type: RSA  # (mandatory) Supported types: ECC, RSA
      size: 4096  # (optional | default :4096) Length of RSA Key (no effect on ECC keys)
      renew: false  # (optional | default: false) Whether to forceufully recreate the key. Will always keep a backup
```

### Directories and permissions

`le_base_directory:` The base directory where to put all generated files (default: /etc/letsencrypt)

`le_files_owner`: Who should own the generated files and folders (default: root)

`le_files_group`: Which group the generated files and folder hould belong to (default: root)

### Let's Encrypt account key

`le_account_key_path`: Where to put (or find) the Let's Encrypt account key (default: "{{ le_base_directory }}/account.key")

`le_account_key_type`: Which key type (RSA, ECC) to use for the account key (default: RSA)

`le_account_key_size`: The size of the key. Only for RSA keys. (default: 4096)

`le_account_key_curve`: Which Curve to use. Only for ECC keys, has no effect for RSA keys. (default: secp384r1)

`le_account_key_regenerate`: Whether to regenerate an existing key or not. Will keep a backup. (default: false)

Unfortunately, Let's Encrypt does not readily support ECC account keys. Best leave it at RSA 4096.

### Let's Encrypt / ACME version and directory

`le_acme_version`: ACME Version to use. Can be neccessary if you choose to use another issuer than Let's Encrypt (default: 2)

`le_acme_directory`: The ACME Directory URL to request certificates at. For safety reasons, the default is set to Let's Encrypt Staging (default: <https://acme-staging-v02.api.letsencrypt.org/directory)>

Let's Encrypt Production Directory is: <https://acme-v02.api.letsencrypt.org/directory.>

`le_renew_if_invalid_after`: Try to renew the certificates if valid for less than this amount of days (default: 30)

`le_force_renew`: try to forcefully renew the certificates (default: false)

`le_csr_only`: If you want to just have private keys and CSRs generated, set this to true. Can be useful for debugging. (default: false)

## Contributing and issues

All contributions are welcome. Don't hesitate to open issues or create pull requests.

I'll gladly look into any issue raised and always try to improve the role.

## Testing

All testing is done with [Molecule](http://molecule.readthedocs.io).

A CI pipeline is realised with GitHub Actions and uses a matrix strategy, which tests on Ubuntu, Debian and CentOS.

To get started with local testing, set up a local Python venv, install all dependencies and run the tests. This requires Docker installed on your machine (or using Docker-Machine):

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r test-requirements.txt

molecule test
```

Since this role essentially requires issuing requests against an ACME server and thus would need control over a domain for which to dynamically set a DNS record, testing is limited to linting,  checking if keys and CSRs get created and are present, and if they contain the expected content.

Testing the complete role with all functionality is done against Let's Encrypt staging server on an actual, internet-connected machine, but manually.

## License

GNU General Public License v3.0
