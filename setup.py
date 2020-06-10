import setuptools

setuptools.setup(
    name="turntaker",
    version="0.0.1",
    author="Laurel Kona Goodhart",
    author_email="code@konahart.com",
    description="A discord bot for playing roleplaying games",
    url="https://github.com/konahart/turn-taker",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)