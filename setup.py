from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()


setup(name='gsmtpd',
        version='0.1',
        license='MIT',
        description='A smtpd server impletement base on Gevent',
        author='Meng Zhuo',
        author_email='mengzhuo1203@gmail.com',
        url='https://github.com/34nm/gsmtpd',
        packages=['gsmtpd'],
        packages_data={'gsmtpd':['README.rst','LICENSE']},
        install_requires=['gevent'],
        classifiers=[
                    'License :: OSI Approved :: MIT License',
                    'Programming Language :: Python :: 2',
                    'Programming Language :: Python :: 2.6',
                    'Programming Language :: Python :: 2.7',
                    'Topic :: Internet :: SMTP Servers',
        ],
        long_description=long_description)
