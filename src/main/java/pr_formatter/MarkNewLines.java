package pr_formatter;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class MarkNewLines
{

	private static final String END_TAG = "// @formatter:on PULL-REQUEST-FORMATTER";

	private static final String START_TAG = "// @formatter:off PULL-REQUEST-FORMATTER";

	static List<Path> markNewLines( Path repository )
	{
		List<FileNewLines> diff = parseDiff( runGitDiff( repository ) );
		for(FileNewLines newLines : diff ) {
			markNewLines( repository.resolve( newLines.file ), newLines.changes );
		}
		return diff.stream().map( s -> s.file ).collect( Collectors.toList());
	}

	private static void markNewLines( Path file, List<Range> changes )
	{
		try
		{
			List<String> content = Files.readAllLines( file, Charset.defaultCharset() );
			List<String> newContent = markNewLines( content, changes );
			Files.write( file, newContent, Charset.defaultCharset() );
		}
		catch ( IOException e )
		{
			throw new RuntimeException( e );
		}
	}

	static List<FileNewLines> parseDiff( List<String> lines )
	{
		List<FileNewLines> files = new ArrayList<>();
		for ( int i = 0; i < lines.size(); i++ )
		{
			if ( lines.get(i).startsWith( "+++ b/" ) )
				files.add( parseDiff( lines, i) );
		}
		return files;
	}

	private static FileNewLines parseDiff( List<String> lines, int i )
	{
		String header = lines.get( i );
		Path file = Paths.get( header.substring( "+++ b/".length() ) );
		List<Range> changes = new ArrayList<>();
		for ( String line : lines.subList( i + 1, lines.size() ) )
		{
			if( line.startsWith( "--- " ) )
				break;
			if( line.startsWith( "@@ " ))
				changes.add( parseRange( line ) );
		}
		return new FileNewLines( file, changes );
	}

	/**
	 * Parses strings like this {@code "@@ -3,4 +5,2 @@ foo bar"}.
	 * The first two integers are ignored. Returns a range created from the
	 * second pair of integers.
	 * For the example above the message would return {@code Range.newStartLength(5,2)}
	 */
	static Range parseRange( String line )
	{
		Pattern pattern = Pattern.compile("@@ -\\d+(,\\d+)? \\+(\\d+)(,(\\d+))? @@.+");
		Matcher matcher = pattern.matcher( line );
		if(!matcher.find())
			throw new IllegalStateException("diff could not be parsed properly");
		int start = Integer.parseInt( matcher.group( 2 ) );
		String lengthString = matcher.group( 4 );
		int length = lengthString == null ? 1 : Integer.parseInt( lengthString );
		return Range.newStartLength( start, length );
	}

	static List<String> runGitDiff( Path repository )
	{
		return RunCommand.runAndGetOutput( repository, "git", "diff", "HEAD~1", "HEAD", "--unified=0" );
	}

	static List<String> markNewLines( List<String> input, List<Range> changes )
	{
		final List<String> output = new ArrayList<>();
		output.add( START_TAG );
		int lineNumber = 0;
		for( Range change : changes ) {
			while( change.start	- 1 > lineNumber )
				output.add(input.get(lineNumber++));
			output.add( END_TAG );
			while( change.end - 1 > lineNumber )
				output.add(input.get(lineNumber++));
			output.add( START_TAG );
		}
		while( lineNumber < input.size() )
			output.add(input.get(lineNumber++));
		return output;
	}

	public static void removeMarks( Path repository, List<Path> files ) {
		for( Path file : files )
			removeMarks( repository.resolve( file ) );
	}

	static void removeMarks( Path file )
	{
		try
		{
			if( ! Files.isRegularFile( file ) )
				throw new IllegalArgumentException( "Expecting regular file but give: " + file );

			List<String> content = Files.readAllLines( file );
			List<String> newContent = removeMarks( content );
			Files.write( file, newContent, Charset.defaultCharset() );
		}
		catch ( IOException e )
		{
			throw new RuntimeException( e );
		}
	}

	static List<String> removeMarks( List<String> content )
	{
		return content.stream()
				.filter( line -> ! END_TAG.equals( line ) && ! START_TAG.equals( line ) )
				.collect( Collectors.toList());
	}
}
