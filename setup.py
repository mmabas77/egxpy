from setuptools import setup


setup(
    name="egxpy",
    version="1.1.0",
    packages=["egxpy"],
    url="https://github.com/omar-Abouyoussef/egxpy/",
    project_urls={
        "Web App": "https://egxpy-lab.streamlit.app/",
        "Source": "https://github.com/omar-Abouyoussef/egxpy/",
        # "Tracker": "https://github.com/omar-Abouyoussef/egxpy/issues",
    },
    license="MIT License",
    author="@omar-Abouyoussef",
    author_email="o.abouyoussef73@gmail.com",
    description="Historical Data And Portfolio Optimization For EGX",
    long_description_content_type="text/markdown",
    install_requires=[
        "setuptools",
        "pandas",
        "numpy",
        "datetime",
        "holidays",
        "retry",
        "tvDatafeed",
        "scipy"
    ],
)
