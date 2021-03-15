#!/usr/bin/env python3
import sys

from samtools_mpileup_tool import multi_samtools_mpileup

if __name__ == "__main__":
    # CLI Entrypoint.
    retcode = 0

    try:
        retcode = multi_samtools_mpileup.main()

    except Exception as e:
        retcode = 1

    sys.exit(retcode)

# __END__
