package expansion;

import java.util.Arrays;
import java.util.List;

/**
 * Expansions for an identifier
 */
public class ParameterNameExpansions extends Expansions {
	private static List<String> key = Arrays.asList("type", "comment", "parameterArgument", "enclosingMethod", "argument", "assignment", "methodInvocated");

	public ParameterNameExpansions() {
		super();
	}

	@Override
	protected void setType() {
		type = "ParameterName";
	}

	@Override
	protected void setKey() {
		expansionKey = key;
	}
}
