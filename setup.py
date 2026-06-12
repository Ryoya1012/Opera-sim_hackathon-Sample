from setuptools import find_packages, setup

package_name = 'task_manager'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ryoya SATO',
    maintainer_email='satoryoya1012711@gmail.com',
    description='TODO: Package description',
    license='Apach-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'hackathon_sample_manager_node = task_manager.hackathon_sample_manager_node:main'
        ],
    },
)
