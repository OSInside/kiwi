<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv64to65">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv64to65"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>6.4</literal> to <literal>6.5</literal>.
</para>
<xsl:template match="image" mode="conv64to65">
    <xsl:choose>
        <!-- nothing to do if already at 6.5 -->
        <xsl:when test="@schemaversion > 6.4">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="6.5">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv64to65"/>  
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<para xmlns="http://docbook.org/ns/docbook">
    Move container attribute from type to containerconfig
</para>
<xsl:template match="type" mode="conv64to65">
    <type>
        <xsl:copy-of select="@*[not(local-name(.) = 'container')]"/>
        <xsl:variable name="container_name" select="@container"/>
        <xsl:if test="$container_name">
            <containerconfig>
                <xsl:attribute name="name">
                    <xsl:value-of select="$container_name"/>
                </xsl:attribute>
            </containerconfig>
        </xsl:if>
        <xsl:apply-templates mode="conv64to65"/>
    </type>
</xsl:template>

</xsl:stylesheet>
