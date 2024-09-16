<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv74to75">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv74to75"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>7.4</literal> to <literal>7.5</literal>.
</para>
<xsl:template match="image" mode="conv74to75">
    <xsl:choose>
        <!-- fail if smaller than 7.4 -->
        <xsl:when test="not(@schemaversion >= 7.4)">
            <xsl:message terminate="yes">Error: Schema version must be >= 7.4 For details how to update older schemas refer to: https://osinside.github.io/kiwi
            </xsl:message>
        </xsl:when>
        <!-- nothing to do if already at 7.5 -->
        <xsl:when test="@schemaversion > 7.4">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="7.5">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv74to75"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv74to75">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv74to75"/>
    </xsl:copy>
</xsl:template>

<!-- rename additionaltags attribute to additionalnames and add a colon before each tag -->
<xsl:template match="containerconfig" mode="conv74to75">
    <containerconfig>
        <xsl:copy-of select="@*[not(local-name(.) = 'additionaltags')]"/>
        <xsl:if test="@additionaltags">
            <xsl:attribute name="additionalnames">
                <xsl:call-template name="replace-all">
                    <xsl:with-param name="text" select="concat(':',@additionaltags)" />
                    <xsl:with-param name="replace" select="','" />
                    <xsl:with-param name="by" select="',:'" />
                </xsl:call-template>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates  mode="conv74to75"/>
    </containerconfig>
</xsl:template>

<!-- replace all ocurrences of a substring template -->
<xsl:template name="replace-all" mode="conv74to75">
    <xsl:param name="text" />
    <xsl:param name="replace" />
    <xsl:param name="by" />
    <xsl:choose>
        <xsl:when test="$text = '' or $replace = ''or not($replace)" >
            <!-- Prevent this routine from hanging -->
            <xsl:value-of select="$text" />
        </xsl:when>
        <xsl:when test="contains($text, $replace)">
            <xsl:value-of select="substring-before($text,$replace)" />
            <xsl:value-of select="$by" />
            <xsl:call-template name="replace-all">
                <xsl:with-param name="text" select="substring-after($text,$replace)" />
                <xsl:with-param name="replace" select="$replace" />
                <xsl:with-param name="by" select="$by" />
            </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
            <xsl:value-of select="$text" />
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
