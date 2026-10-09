from setuptools import setup, find_packages

setup(
    name="aasi-client",
    version="0.3.0",
    description="Autonomous Aerospace Scientific Intelligence (AASI) Python SDK",
    long_description="Enterprise client for AASI physics AI surrogates, Navier-Stokes CFD orchestrators, and ASME V&V 20 certification.",
    author="AASI Aerospace Systems",
    author_email="dev@aasi-aerospace.com",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "aasi=aasi_client.cli:main",
        ],
    },
)

