import click, sys, statistics
from subprocess import run, PIPE

def format_hicrep(hicrep_args, hicrep_out, read, process):
    if hicrep_args is None:
        return ""
    hicrep_start = ' '.join(["hicrep {1} {2}", hicrep_out])
    silencer = " 2> /dev/null"
    read_cmd = f"; cat {hicrep_out}" if read else ""

    if process is None:
        process = ""
    elif process == "scc-mean":
        process = "| python -m vs_hicrep.scc_mean"
    elif process == "scc-scores":
        process = "| python -m vs_hicrep.scc_scores"
    elif process != "":
        process = "| " + process
    return ' '.join([hicrep_start, hicrep_args, silencer, read_cmd, process])


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--hicrep",
    default="--h 1 --binSize 500000 --dBPMax 1000000",
    help="hicrep parameters to run on piped-in files")
@click.option("--hicrep-md", help="Alternative hicrep parameters to run on main diagonal")
@click.option("--hicrep-slt", help="Alternative hicrep parameters to run on lower matrix triangle")
@click.option("--row", default="pathlib-cli prefix {1}", help=r"Terminal command to transform .mcool row file path ({1}) to row caption")
@click.option("--col", default="pathlib-cli prefix {2}", help=r"Terminal command to transform .mcool column file path ({2}) to column caption")
@click.option("--hicrep-out", default="scc/{3}_{4}.txt", help=r"Path to save SCC score files. Use {1} and {2} for row and column paths, {3} and {4} for row/col captions.")
@click.option("--read/--no-read", is_flag=True, default=True, help="If --read is set, load output SCC scores to pandas dataframe.")
@click.option("--hicrep-process", default="scc-mean", help="If not blank, raw output from hicrep SCC score files will be piped to this command. Command output captured and stored in dataframe in each cell.")
@click.option("--md-process", default="scc-mean", help="Define a different process for the main diagonal.")
@click.option("--slt-process", default="scc-mean", help="Define a different process for the strictly lower triangle.")
@click.option("--mkdir/--no-mkdir", is_flag=True, default=True, help="Make directory for output SCC scores (hicrep will only do this automatically if new dir's parent already exists)")
@click.option("--dryrun", is_flag=True, help="Generate dataframe containing commands to run to compute hicrep scores, but don't actually run those commands.")
def cli(ctx, hicrep, hicrep_md, hicrep_slt, row, col, hicrep_out, read, hicrep_process, md_process, slt_process, mkdir, dryrun):
    """
    hicrep-wistan
    - Generate YAMLized pandas DataFrame with sample vs. sample hicrep scores, means, other statistics
    - Compare two sets of hicrep parameters on upper and lower matrix (i.e. two chromosomes or two resolutions)
    - Visualize with Seaborn clustermap in Jupyter Notebook
    - Record analysis parameters for future reference

    The output dataframe contains not only the mean result, but also the
    hicrep command used to generate results, the raw contents of each SCC score file,
    the SCC score summary statistic (mean by default), and other data.

    It is recommended to redirect the immediate output to a file with `> [hicrep data filename].yaml`

    You can extract just the summary statistic with `pandas-cli --layer result`.
    - To output to markdown for viewing in the terminal, pipe results `pandas-cli --layer result to markdown`.
    - To output to a YAMLized pandas DataFrame for loading into a Jupyter notebook with Wistan's dataframe-vis-nb,
      pipe results to `pandas-cli --layer result to dict > [output name].ipynb`. You can then insert code to generate
      a clustermap of the results into a Jupyter notebook with `dataframe-vis-nb [notebook name] [cell index] clustermap [results.yaml].
    

    Examples:

    ls *.mcool | hicrep-wistan > hicrep_data.yaml

    L--> Generates hicrep score means for all .mcool files in the current directory. Saves record of how data was generated,
    along with raw output and summary statistics, to `hicrep_data.yaml`, putting raw SCC score files in scc/[prefix1]_[prefix2].txt.
    Uses default --h 1 --binSize 500000 --dBPMax 5000000.

    ls *.mcool | hicrep-wistan --hicrep "--h 1 --binSize 100000 --dBPMax 5000000 --chrNames chr1 chr2 chr3" > hicrep_data.yaml

    L--> Specify bin size of 100kb, only computing SCC scores for chr1-3

    ls *.mcool | hicrep-wistan --hicrep "--h 1 --binSize 500000 --dBPMax 5000000"
                               --hicrep-slt "--h 1 --binSize 100000 --dBPMax 5000000"  > hicrep_data.yaml
    
    L--> Compare all chromosome means at bin sizes of 500kb (upper triangle of dataframe and main diagonal) and 100kb (strictly lower triangle)

    ls *.mcool | hicrep-wistan | pandas-cli --layer result to markdown

    L--> Extract just the per-chromosome means and display in markdown in the terminal

    ls *.mcool | hicrep-wistan > hicrep_data.yaml && cat hicrep_data.yaml | pandas-cli --layer result to dict > hicrep_result.yaml &&
                dataframe-vis-nb notebook.ipynb 0 clustermap hicrep_result.yaml
    
    L--> Extract just the per-chromosome means, save to a new YAMLized dataframe in hicrep_result.yaml, then generate code to load
    them into a Jupyter notebook and display as a Seaborn clustermap.

    hicrep.py: https://github.com/dejunlin/hicrep
    """
    if mkdir:
        cmd = ["pathlib-cli", "parent", hicrep_out]
        dir = run(cmd, input = hicrep_out, stdout = PIPE, text=True, check=True).stdout.strip()
        cmd = ["mkdir", "-p", dir]
        run(cmd, text=True, check=True)
    
    hicrep_sut_command = format_hicrep(hicrep, hicrep_out, read, hicrep_process)

    cmd = [ "versus-cli", row, col, hicrep_sut_command, "--caption-index", "2", "3"]
    if hicrep_md is not None:
        hicrep_md_command = format_hicrep(hicrep_md, hicrep_out, read, md_process)
        cmd += ["--md-command", hicrep_md_command]
    if hicrep_slt is not None:
        hicrep_slt_command = format_hicrep(hicrep_slt, hicrep_out, read, slt_process)
        cmd += ["--slt-command", hicrep_slt_command]

    if dryrun:
        cmd += ["--dryrun", "--echo-args"]

    result = run(cmd, input=sys.stdin.read(), stdout = PIPE, text=True, check=True).stdout

    if ctx.invoked_subcommand is None:
        click.echo(result)
    else:
        ctx.obj['RESULT'] = result

@cli.group()
@click.pass_context
def to(ctx):
    pass

@to.command()
@click.pass_context
def markdown(ctx):
    run(["pandas-cli", "--layer", "result", "to", "markdown"], input=ctx.obj['RESULT'], text=True, check=True)

@to.command()
@click.pass_context
@click.argument("notebook")
@click.option("--append_after", default='0')
@click.option("--result-file", default="vs-hicrep-results.yaml")
def notebook(ctx, notebook, append_after, result_file):
    cmd = ["pandas-cli",
            "--layer",
            "result",
            "to",
            "dict"]
    result = run(cmd, input=ctx.obj['RESULT'], stdout = PIPE, text=True, check=True).stdout
    open(result_file, "w").write(result)
    cmd = ["dataframe-vis-nb",
    notebook,
    append_after,
    "clustermap",
    result_file]
    run(cmd, input=result, text=True, check=True)


if __name__ == "__main__":
    cli(obj={})