"""Include build-environment Python package versions and supplied licenses."""
from importlib.metadata import distributions
from pathlib import Path
import sys


def write_notices(destination):
    sections=[]
    for distribution in sorted(distributions(),key=lambda d:d.metadata['Name'].casefold()):
        name=distribution.metadata['Name']
        sections.append(f'\n{name} {distribution.version}\n'+str(distribution.metadata.get('License-Expression') or distribution.metadata.get('License') or 'See supplied license text / upstream project.'))
        for file in distribution.files or []:
            if any(part.endswith(('.dist-info','.egg-info')) for part in file.parts) and file.name.lower().startswith(('license','copying','notice','authors')):
                path=distribution.locate_file(file)
                if path.is_file(): sections.append(str(file)+'\n'+path.read_text(encoding='utf-8',errors='replace'))
    Path(destination).write_text('\n\n'.join(sections),encoding='utf-8')


if __name__=='__main__': write_notices(sys.argv[1])
