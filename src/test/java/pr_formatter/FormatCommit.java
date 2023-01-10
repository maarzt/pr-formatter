package pr_formatter;

import java.nio.file.Path;
import java.util.List;

public class FormatCommit
{
	public static void forRepository( Path repository ) {
		List<Path> modifiedFiles = MarkNewLines.markNewLines( repository );
		RunCommand.runAndGetOutput( repository, "mvn", "formatter:format" );
		MarkNewLines.removeMarks( repository, modifiedFiles );
		gitAmendFiles( repository, modifiedFiles );
		gitResetHard( repository );
	}

	private static void gitAmendFiles( Path repository, List<Path> files )
	{
		for( Path file : files )
			RunCommand.runAndGetOutput( repository, "git", "add", file.toString() );
		RunCommand.runAndGetOutput( repository, "git", "commit", "-C", "HEAD", "--amend" );
	}

	private static void gitResetHard( Path repository )
	{
		RunCommand.runAndGetOutput( repository, "git", "reset", "--hard", "HEAD" );
	}
}
