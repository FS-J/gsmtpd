from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

with open('requirements.txt') as require:

    setup(name='gsmtpd',
            version='0.1.5',
            license='MIT',
            description='A smtpd server impletement base on Gevent',
            author='Meng Zhuo',
            author_email='mengzhuo1203@gmail.com',
            url='https://github.com/34nm/gsmtpd',
            packages=['gsmtpd'],
            install_requires=[line for line in require.readlines()],
            classifiers=[
                        'License :: OSI Approved :: MIT License',
                        'Programming Language :: Python :: 2',
                        'Programming Language :: Python :: 2.6',
                        'Programming Language :: Python :: 2.7',
                        'Topic :: Communications :: Email :: Mail Transport Agents',
                        'Topic :: Communications :: Email'
            ],
            long_description=long_description)
