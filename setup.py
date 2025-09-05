import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="acrome-smd-beta",
    version="0.0.4",
    author="BeratComputer",
    author_email="beratdogan@acrome.net",
    description="Python library for interfacing with Acrome Robotic Arm Joint BLDC Motor Controllers (Beta Version) \n \n This Python library provides an easy-to-use interface for communication and control of BLDC motor controllers used in Acrome robotic arm joints. It is designed to simplify the integration of Acrome’s robotic joint actuators into custom applications, allowing developers and researchers to focus on building advanced robotic systems without dealing with low-level communication details.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Acrome-Smart-Motion-Devices/python-library-new",
    project_urls={
        "Bug Tracker": "https://github.com/Acrome-Smart-Motion-Devices/python-library/issues",
        },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(exclude=['tests', 'test']),
    install_requires=["pyserial>=3.5", "stm32loader>=0.5.1", "crccheck>=1.3.0", "requests>=2.31.0", "packaging>=23.2"],
    python_requires=">=3.7"
)