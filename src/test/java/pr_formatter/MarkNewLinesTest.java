package pr_formatter;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import org.junit.Test;

public class MarkNewLinesTest
{

	private final String file = "src/main/java/org/mastodon/mamut/model/branch/ModelBranchGraph.java";

	private final List<Range> expectedChanges = Arrays.asList(
			Range.newStartLength( 40, 2 ),
			Range.newStartLength( 52, 1 ),
			Range.newStartLength( 64, 5 ),
			Range.newStartLength( 80, 27 ) );

	private final FileNewLines expectedFileChange = new FileNewLines( Paths.get( file ), expectedChanges );

	@Test
	public void testGetRange() {
		assertEquals( new Range( 3, 7 ), MarkNewLines.parseRange( "@@ -1,2 +3,4 @@ foo bar" ) );
		assertEquals( new Range( 3, 4 ), MarkNewLines.parseRange( "@@ -1,2 +3 @@ hello" ) );
		assertEquals( new Range( 77, 78 ), MarkNewLines.parseRange( "@@ -66 +77 @@ world" ) );
	}

	@Test
	public void testParseDiff() throws IOException
	{
		List<String> lines = Arrays.asList(
				"diff --git a/folder/foo_bar.txt b/folder/foo_bar.txt",
				"index 7cd175ac3..b4ca3e370 100644",
				"--- a/folder/foo_bar.txt",
				"+++ b/folder/foo_bar.txt",
				"@@ -2 +2 @@ foo",
				"-bar",
				"+Hello World!",
				"@@ -77,0 +79 @@ foo",
				"+foo bar"
		);
		FileNewLines modifications = new FileNewLines(
				Paths.get("folder/foo_bar.txt" ),
				Range.newStartLength( 2, 1 ),
				Range.newStartLength( 79,1 )
		);
		assertEquals( Collections.singletonList( modifications ), MarkNewLines.parseDiff( lines ) );
	}

	@Test
	public void testMarkNewLines() throws IOException
	{
		List<String> input = Files.readAllLines( Paths.get( "src/test/resources/example.java" ) );
		List<String> output = MarkNewLines.markNewLines(input, expectedFileChange.changes);
		List<String> expected = Files.readAllLines( Paths.get( "src/test/resources/expected.java" ) );
		assertEquals(expected, output);
	}

}
