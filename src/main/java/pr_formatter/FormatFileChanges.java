package pr_formatter;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.List;

import org.apache.commons.io.FileUtils;

public class FormatFileChanges
{
	public static List<String> formatJavaCode( Path mvnFile, List<String> input )
			throws IOException
	{
		Path tmpRoot = Files.createTempDirectory( "tmp-mv-project" );
		Path javaFolder = Files.createDirectories( tmpRoot.resolve( "src/main/java" ) );
		Files.copy( mvnFile, tmpRoot.resolve( "pom.xml" ) );
		Path path = javaFolder.resolve( "test.java" );
		Files.write( path, input );
		RunCommand.runAndGetOutput( tmpRoot, "mvn", "formatter:format" );
		List<String> output = Files.readAllLines( path );
		FileUtils.deleteDirectory( tmpRoot.toFile() );
		return output;
	}

	public static void formatOnlyChangesInJavaCode( Path pomXml, Path originalJava, Path changedJava, Path formattedChangedJava )
			throws IOException
	{
		List<String> diff = RunCommand.runAndGetOutput( Paths.get( "." ), "git", "diff", "--no-index", "--unified=0", originalJava.toString(), changedJava.toString() );
		List<FileNewLines> changesForEachFile = MarkNewLines.parseDiff( diff );
		if(changesForEachFile.isEmpty()) {
			Files.copy( changedJava, formattedChangedJava, StandardCopyOption.REPLACE_EXISTING );
			return;
		}
		if(changesForEachFile.size() > 1)
			throw new AssertionError();
		List<Range> changes = changesForEachFile.get(0).changes;
		List<String> preprocessedJava = MarkNewLines.markNewLines( Files.readAllLines( changedJava ), changes );
		List<String> formattedJava = formatJavaCode( pomXml, preprocessedJava );
		List<String> postprocessedJava = MarkNewLines.removeMarks( formattedJava );
		Files.write( formattedChangedJava, postprocessedJava );
	}

	public static void main(String... args) throws IOException
	{
		Path pomXml = Paths.get( args[0] );
		Path original = Paths.get( args[1] );
		Path changed = Paths.get( args[2] );
		Path output = Paths.get( args[3] );
		formatOnlyChangesInJavaCode( pomXml, original, changed, output );
	}
}
