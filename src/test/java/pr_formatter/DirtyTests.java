package pr_formatter;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

import org.junit.Ignore;
import org.junit.Test;

public class DirtyTests
{
	private final Path repository = Paths.get("/home/arzt/devel/pull-request-formatter/mastodon");

	@Ignore("not reproducible, no test")
	@Test
	public void testGetDiff() {
		final List<String> diff = MarkNewLines.runGitDiff(repository);
		diff.forEach( System.out::println );
	}

	@Ignore
	@Test
	public void testFormatCommit() {
		FormatCommit.forRepository( repository );
	}
}
