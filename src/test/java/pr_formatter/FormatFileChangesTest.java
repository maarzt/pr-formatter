package pr_formatter;

import static org.junit.Assert.assertEquals;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import org.junit.Test;

public class FormatFileChangesTest
{
	private final Path pomXml = Paths.get("pom.xml");
	private final Path originalJava = Paths.get("src/test/resources/simple_example/original.java");
	private final Path changedJava = Paths.get("src/test/resources/simple_example/modified.java");
	private final Path expectedJava = Paths.get("src/test/resources/simple_example/expected.java");

	@Test
	public void testFormatJavaCode() throws IOException
	{
		// create temporary mvn repository
		Path mvnFile = Paths.get("pom.xml");
		List<String> input = Collections.singletonList(
				"class Something { boolean test() { return true; } }" );
		List<String> formatted = FormatFileChanges.formatJavaCode( mvnFile, input );
		List<String> expected = Arrays.asList(
				"class Something {",
				"",
				"	boolean test() {",
				"		return true;",
				"	}",
				"}"
		);
		assertEquals(expected, formatted);
	}

	@Test
	public void testFormatChanges() throws IOException
	{
		Path resultJava = Files.createTempFile( "formatted", ".java" );
		try
		{
			FormatFileChanges.formatOnlyChangesInJavaCode( pomXml, originalJava, changedJava, resultJava );
			assertEquals( Files.readAllLines( expectedJava ), Files.readAllLines( resultJava ) );
		}
		finally {
			Files.delete( resultJava );
		}
	}

	@Test
	public void testNoChanges() throws IOException
	{
		Path resultJava = Files.createTempFile( "formatted", ".java" );
		try
		{
			FormatFileChanges.formatOnlyChangesInJavaCode( pomXml, originalJava, originalJava, resultJava );
			assertEquals( Files.readAllLines( originalJava ), Files.readAllLines( resultJava ) );
		}
		finally {
			Files.delete( resultJava );
		}
	}

}
