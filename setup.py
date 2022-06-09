from setuptools import find_packages, setup
setup(
    name="smslib",
    packages=find_packages(include=["smslib"]),
    version="0.1.14",
    description="An internal library to send boardon sms messages",
    author="Patrick Minogue",
    install_requires=['mailjet-rest==1.3.4',
                      'requests==2.25.1', 'mysql-connector-python==8.0.23'],
    license="MIT",
)
